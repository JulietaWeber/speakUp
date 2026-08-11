const supabase = require("../config/Supabase");

const obtenerUsuarios = async (req, res) => {

  const { data, error } = await supabase
    .from("usuarios")
    .select("*");

  res.json({ data, error });

};

const crearUsuario = async (req, res) => {

  const {
    nombre,
    email,
    password,
    rol,
    foto_perfil,
    ultima_sincronizacion
  } = req.body;

  const { data, error } = await supabase
    .from("usuarios")
    .insert([
      {
        nombre,
        email,
        password,
        rol,
        foto_perfil,
        ultima_sincronizacion
      }
    ]);

  res.json({
    message: "Usuario creado correctamente",
    data,
    error
  });

};

const obtenerUsuarioPorId = async (req, res) => {

  const { id } = req.params;

  const { data, error } = await supabase
    .from("usuarios")
    .select("*")
    .eq("id_usuario", id)
    .single();

  res.json({ data, error });
};

const actualizarUsuario = async (req, res) => {

  const { id } = req.params;

  const {
    nombre,
    email,
    password,
    rol,
    foto_perfil,
    ultima_sincronizacion
  } = req.body;

  const { data, error } = await supabase
    .from("usuarios")
    .update({
      nombre,
      email,
      password,
      rol,
      foto_perfil,
      ultima_sincronizacion
    })
    .eq("id_usuario", id);

  res.json({ data, error });
};

const eliminarUsuario = async (req, res) => {

  const { id } = req.params;

  const { data, error } = await supabase
    .from("usuarios")
    .delete()
    .eq("id_usuario", id);

  res.json({ data, error });
};

const obtenerTablerosDeUsuario = async (req, res) => {

  const { id } = req.params;

  const { data, error } = await supabase
    .from("tableros")
    .select("*")
    .eq("id_usuario", id);

  res.json({
    data,
    error
  });

};

const subirFotoPerfil = async (req, res) => {
  try {
    const id_usuario = req.usuario.id_usuario;

    if (!req.file) {
      return res.status(400).json({
        data: null,
        error: "Tenés que enviar una imagen en el campo foto"
      });
    }

    const extension = req.file.originalname.split(".").pop();
    const nombreArchivo = `usuario-${id_usuario}-${Date.now()}.${extension}`;
    const rutaArchivo = `${id_usuario}/${nombreArchivo}`;

    const { error: uploadError } = await supabase.storage
      .from("usuarios-fotos")
      .upload(rutaArchivo, req.file.buffer, {
        contentType: req.file.mimetype,
        upsert: true
      });

    if (uploadError) {
      return res.status(500).json({
        data: null,
        error: uploadError.message
      });
    }

    const { data: publicUrlData } = supabase.storage
      .from("usuarios-fotos")
      .getPublicUrl(rutaArchivo);

    const foto_perfil = publicUrlData.publicUrl;

    const { data: usuarioActualizado, error: updateError } = await supabase
      .from("usuarios")
      .update({ foto_perfil })
      .eq("id_usuario", id_usuario)
      .select("id_usuario, nombre, email, rol, foto_perfil")
      .single();

    if (updateError) {
      return res.status(500).json({
        data: null,
        error: updateError.message
      });
    }

    await supabase.from("historial_uso").insert([
      {
        id_usuario,
        accion: "subir_foto_perfil",
        detalle: "Foto de perfil actualizada"
      }
    ]);

    return res.json({
      data: usuarioActualizado,
      error: null
    });

  } catch (error) {
    return res.status(500).json({
      data: null,
      error: error.message
    });
  }
};

const obtenerPerfil = async (req, res) => {
  try {
    const id_usuario = req.usuario.id_usuario;

    const { data: usuario, error } = await supabase
      .from("usuarios")
      .select("id_usuario, nombre, email, rol, foto_perfil")
      .eq("id_usuario", id_usuario)
      .single();

    if (error) {
      return res.status(500).json({
        data: null,
        error: error.message
      });
    }

    return res.json({
      data: usuario,
      error: null
    });

  } catch (error) {
    return res.status(500).json({
      data: null,
      error: error.message
    });
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
  obtenerPerfil
};