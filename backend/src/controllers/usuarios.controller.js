const bcrypt = require("bcryptjs");
const supabase = require("../config/Supabase");
const supabaseAdmin = require("../config/SupabaseAdmin");
const { existeVoz, VOZ_DEFAULT } = require("../config/voces");

const CAMPOS_USUARIO = "id_usuario, nombre, email, rol, foto_perfil, voz_preferida";
const responderOk = (res, data, status = 200) => res.status(status).json({ data, error: null });
const responderError = (res, status, error) => res.status(status).json({ data: null, error });
const validarId = (id) => Number.isSafeInteger(Number(id)) && Number(id) > 0;
const emailValido = (email) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
const passwordValida = (password) =>
  typeof password === "string" && password.length >= 8 && /[A-Z]/.test(password) && /[^A-Za-z0-9]/.test(password);

const cargarUsuario = async (id) => {
  const { data, error } = await supabaseAdmin.from("usuarios")
    .select(CAMPOS_USUARIO).eq("id_usuario", id).maybeSingle();
  if (error) throw error;
  return data;
};

// Leer el rol actual de la base, no confiar en el rol que quedó guardado en un JWT antiguo.
const verificarAcceso = async (req, res, idObjetivo, adminObligatorio = false) => {
  const solicitante = await cargarUsuario(req.usuario.id_usuario);
  if (!solicitante) {
    responderError(res, 401, "Usuario no encontrado o sesión inválida");
    return false;
  }
  if (adminObligatorio ? solicitante.rol !== "admin" :
      solicitante.rol !== "admin" && Number(solicitante.id_usuario) !== Number(idObjetivo)) {
    responderError(res, 403, "No tenés permiso para realizar esta acción");
    return false;
  }
  return true;
};

const registrarHistorial = async (id_usuario, accion, detalle) => {
  const { error } = await supabaseAdmin.from("historial_uso")
    .insert([{ id_usuario, accion, detalle }]);
  if (error) console.error("No se pudo registrar historial:", error.message);
};

// GET /usuarios (solo admin)
const obtenerUsuarios = async (req, res) => {
  try {
    if (!(await verificarAcceso(req, res, null, true))) return;
    const { data, error } = await supabaseAdmin.from("usuarios")
      .select(CAMPOS_USUARIO).order("id_usuario", { ascending: true });
    if (error) throw error;
    return responderOk(res, data);
  } catch (error) {
    console.error("obtenerUsuarios:", error);
    return responderError(res, 500, "No se pudieron obtener los usuarios");
  }
};

// POST /usuarios (solo admin; el registro normal sigue en /auth/register)
const crearUsuario = async (req, res) => {
  try {
    if (!(await verificarAcceso(req, res, null, true))) return;
    const { nombre, email, password, rol = "usuario" } = req.body || {};
    const nombreLimpio = typeof nombre === "string" ? nombre.trim() : "";
    const emailLimpio = typeof email === "string" ? email.trim().toLowerCase() : "";
    if (!nombreLimpio || !emailValido(emailLimpio) || !passwordValida(password)) {
      return responderError(res, 400, "Ingresá nombre, email válido y contraseña de 8 caracteres con mayúscula y carácter especial");
    }
    if (!["usuario", "admin"].includes(rol)) return responderError(res, 400, "Rol inválido");
    const { data: existente, error: buscarError } = await supabaseAdmin.from("usuarios")
      .select("id_usuario").eq("email", emailLimpio).maybeSingle();
    if (buscarError) throw buscarError;
    if (existente) return responderError(res, 409, "Ya existe un usuario con ese email");
    const { data, error } = await supabaseAdmin.from("usuarios")
      .insert([{ nombre: nombreLimpio, email: emailLimpio, password: await bcrypt.hash(password, 10), rol, voz_preferida: VOZ_DEFAULT }])
      .select(CAMPOS_USUARIO).single();
    if (error) throw error;
    return responderOk(res, data, 201);
  } catch (error) {
    console.error("crearUsuario:", error);
    return responderError(res, 500, "No se pudo crear el usuario");
  }
};

// GET /usuarios/:id (propio o admin)
const obtenerUsuarioPorId = async (req, res) => {
  try {
    const { id } = req.params;
    if (!validarId(id)) return responderError(res, 400, "ID de usuario inválido");
    if (!(await verificarAcceso(req, res, id))) return;
    const usuario = await cargarUsuario(id);
    if (!usuario) return responderError(res, 404, "Usuario no encontrado");
    return responderOk(res, usuario);
  } catch (error) {
    console.error("obtenerUsuarioPorId:", error);
    return responderError(res, 500, "No se pudo obtener el usuario");
  }
};

// PUT /usuarios/:id (propio o admin). NO permite rol/password/foto/voz en este endpoint.
const actualizarUsuario = async (req, res) => {
  try {
    const { id } = req.params;
    if (!validarId(id)) return responderError(res, 400, "ID de usuario inválido");
    if (!(await verificarAcceso(req, res, id))) return;
    const body = req.body || {};
    const camposProhibidos = ["password", "rol", "foto_perfil", "voz_preferida", "google_id", "id_usuario"];
    if (camposProhibidos.some((campo) => Object.prototype.hasOwnProperty.call(body, campo))) {
      return responderError(res, 400, "Usá los endpoints específicos para contraseña, foto o voz; no se puede cambiar el rol acá");
    }
    const datos = {};
    if (body.nombre !== undefined) {
      if (typeof body.nombre !== "string" || !body.nombre.trim()) return responderError(res, 400, "Nombre inválido");
      datos.nombre = body.nombre.trim();
    }
    if (body.email !== undefined) {
      if (typeof body.email !== "string" || !emailValido(body.email.trim())) return responderError(res, 400, "Email inválido");
      datos.email = body.email.trim().toLowerCase();
    }
    if (!Object.keys(datos).length) return responderError(res, 400, "No hay datos para actualizar");
    const { data, error } = await supabaseAdmin.from("usuarios")
      .update(datos).eq("id_usuario", id).select(CAMPOS_USUARIO).maybeSingle();
    if (error) {
      if (error.code === "23505") return responderError(res, 409, "Ese email ya está registrado");
      throw error;
    }
    if (!data) return responderError(res, 404, "Usuario no encontrado");
    return responderOk(res, data);
  } catch (error) {
    console.error("actualizarUsuario:", error);
    return responderError(res, 500, "No se pudo actualizar el usuario");
  }
};

// PUT /usuarios/voz (solo propio, a partir del JWT)
const actualizarVozPreferida = async (req, res) => {
  try {
    const id_usuario = req.usuario.id_usuario;
    const { voz_preferida } = req.body || {};
    if (!voz_preferida) return responderError(res, 400, "Falta la voz_preferida");
    if (!existeVoz(voz_preferida)) return responderError(res, 400, "La voz seleccionada no es válida");
    const { data, error } = await supabaseAdmin.from("usuarios")
      .update({ voz_preferida }).eq("id_usuario", id_usuario)
      .select(CAMPOS_USUARIO).maybeSingle();
    if (error) throw error;
    if (!data) return responderError(res, 404, "Usuario no encontrado");
    await registrarHistorial(id_usuario, "actualizar_voz_preferida", `Voz preferida actualizada a: ${voz_preferida}`);
    return responderOk(res, data);
  } catch (error) {
    console.error("actualizarVozPreferida:", error);
    return responderError(res, 500, "No se pudo actualizar la voz");
  }
};

// DELETE /usuarios/:id (solo admin)
const eliminarUsuario = async (req, res) => {
  try {
    const { id } = req.params;
    if (!validarId(id)) return responderError(res, 400, "ID de usuario inválido");
    if (!(await verificarAcceso(req, res, id, true))) return;
    if (Number(req.usuario.id_usuario) === Number(id)) {
      return responderError(res, 400, "No podés eliminar tu propia cuenta desde esta ruta");
    }
    const { data, error } = await supabaseAdmin.from("usuarios")
      .delete().eq("id_usuario", id).select("id_usuario").maybeSingle();
    if (error) throw error;
    if (!data) return responderError(res, 404, "Usuario no encontrado");
    return responderOk(res, "Usuario eliminado correctamente");
  } catch (error) {
    console.error("eliminarUsuario:", error);
    return responderError(res, 500, "No se pudo eliminar el usuario");
  }
};

// GET /usuarios/:id/tableros (propio o admin)
const obtenerTablerosDeUsuario = async (req, res) => {
  try {
    const { id } = req.params;
    if (!validarId(id)) return responderError(res, 400, "ID de usuario inválido");
    if (!(await verificarAcceso(req, res, id))) return;
    const { data, error } = await supabaseAdmin.from("tableros")
      .select("*").eq("id_usuario", id).order("fecha_creacion", { ascending: false });
    if (error) throw error;
    return responderOk(res, data);
  } catch (error) {
    console.error("obtenerTablerosDeUsuario:", error);
    return responderError(res, 500, "No se pudieron obtener los tableros");
  }
};

// GET /usuarios/perfil/me
const obtenerPerfil = async (req, res) => {
  try {
    const usuario = await cargarUsuario(req.usuario.id_usuario);
    if (!usuario) return responderError(res, 404, "Usuario no encontrado");
    return responderOk(res, usuario);
  } catch (error) {
    console.error("obtenerPerfil:", error);
    return responderError(res, 500, "No se pudo obtener el perfil");
  }
};

// POST /usuarios/foto-perfil
const subirFotoPerfil = async (req, res) => {
  try {
    const id_usuario = req.usuario.id_usuario;
    if (!req.file) return responderError(res, 400, "Tenés que enviar una imagen en el campo foto");
    const extensiones = { jpeg: "jpg", jpg: "jpg", jfif: "jpg", png: "png", webp: "webp" };
    const extensionOriginal = String(req.file.originalname).split(".").pop().toLowerCase();
    const extension = extensiones[extensionOriginal];
    const tiposPermitidos = ["image/jpeg", "image/png", "image/webp", "image/pjpeg", "image/jpg"];
    if (!extension || !tiposPermitidos.includes(req.file.mimetype)) {
      return responderError(res, 400, "Formato de imagen no permitido");
    }
    const rutaArchivo = `${id_usuario}/usuario-${id_usuario}-${Date.now()}.${extension}`;
    const { error: uploadError } = await supabaseAdmin.storage.from("usuarios-fotos")
      .upload(rutaArchivo, req.file.buffer, { contentType: req.file.mimetype, upsert: false });
    if (uploadError) throw uploadError;
    const { data: publicUrl } = supabaseAdmin.storage.from("usuarios-fotos").getPublicUrl(rutaArchivo);
    const { data, error } = await supabaseAdmin.from("usuarios")
      .update({ foto_perfil: publicUrl.publicUrl }).eq("id_usuario", id_usuario)
      .select(CAMPOS_USUARIO).maybeSingle();
    if (error || !data) {
      await supabaseAdmin.storage.from("usuarios-fotos").remove([rutaArchivo]);
      if (error) throw error;
      return responderError(res, 404, "Usuario no encontrado");
    }
    await registrarHistorial(id_usuario, "subir_foto_perfil", "Foto de perfil actualizada");
    return responderOk(res, data);
  } catch (error) {
    console.error("subirFotoPerfil:", error);
    return responderError(res, 500, "No se pudo subir la foto de perfil");
  }
};

// DELETE /usuarios/foto-perfil
const eliminarFotoPerfil = async (req, res) => {
  try {
    const id_usuario = req.usuario.id_usuario;
    const usuario = await cargarUsuario(id_usuario);
    if (!usuario) return responderError(res, 404, "Usuario no encontrado");
    if (!usuario.foto_perfil) return responderOk(res, usuario);
    const { data, error } = await supabaseAdmin.from("usuarios")
      .update({ foto_perfil: null }).eq("id_usuario", id_usuario)
      .select(CAMPOS_USUARIO).maybeSingle();
    if (error) throw error;
    if (!data) return responderError(res, 404, "Usuario no encontrado");
    await registrarHistorial(id_usuario, "eliminar_foto_perfil", "Foto de perfil eliminada");
    return responderOk(res, data);
  } catch (error) {
    console.error("eliminarFotoPerfil:", error);
    return responderError(res, 500, "No se pudo eliminar la foto de perfil");
  }
};

module.exports = {
  obtenerUsuarios,
  crearUsuario,
  obtenerUsuarioPorId,
  actualizarUsuario,
  eliminarUsuario,
  obtenerTablerosDeUsuario,
  subirFotoPerfil,
  eliminarFotoPerfil,
  obtenerPerfil,
  actualizarVozPreferida
};
