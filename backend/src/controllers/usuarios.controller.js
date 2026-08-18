const supabase = require("../config/Supabase");
const supabaseAdmin = require("../config/SupabaseAdmin");

// GET /usuarios
const obtenerUsuarios = async (req, res) => {
  try {
    const { data, error } = await supabase
      .from("usuarios")
      .select("id_usuario, nombre, email, rol, foto_perfil")
      .order("id_usuario", { ascending: true });

    if (error) {
      return res.status(500).json({
        data: null,
        error: error.message
      });
    }

    return res.json({
      data,
      error: null
    });

  } catch (error) {
    return res.status(500).json({
      data: null,
      error: error.message
    });
  }
};

// POST /usuarios
const crearUsuario = async (req, res) => {
  try {
    const {
      nombre,
      email,
      password,
      rol
    } = req.body;

    if (!nombre || !email || !password) {
      return res.status(400).json({
        data: null,
        error: "Faltan datos obligatorios: nombre, email o password"
      });
    }

    const { data, error } = await supabase
      .from("usuarios")
      .insert([
        {
          nombre,
          email,
          password,
          rol: rol || "usuario"
        }
      ])
      .select("id_usuario, nombre, email, rol, foto_perfil")
      .single();

    if (error) {
      return res.status(500).json({
        data: null,
        error: error.message
      });
    }

    return res.status(201).json({
      data,
      error: null
    });

  } catch (error) {
    return res.status(500).json({
      data: null,
      error: error.message
    });
  }
};

// GET /usuarios/:id
const obtenerUsuarioPorId = async (req, res) => {
  try {
    const { id } = req.params;

    const { data, error } = await supabase
      .from("usuarios")
      .select("id_usuario, nombre, email, rol, foto_perfil")
      .eq("id_usuario", id)
      .single();

    if (error) {
      return res.status(404).json({
        data: null,
        error: "Usuario no encontrado"
      });
    }

    return res.json({
      data,
      error: null
    });

  } catch (error) {
    return res.status(500).json({
      data: null,
      error: error.message
    });
  }
};

// PUT /usuarios/:id
const actualizarUsuario = async (req, res) => {
  try {
    const { id } = req.params;

    const {
      nombre,
      email,
      password,
      rol,
      foto_perfil
    } = req.body;

    const datosActualizar = {};

    if (nombre !== undefined) datosActualizar.nombre = nombre;
    if (email !== undefined) datosActualizar.email = email;
    if (password !== undefined) datosActualizar.password = password;
    if (rol !== undefined) datosActualizar.rol = rol;
    if (foto_perfil !== undefined) datosActualizar.foto_perfil = foto_perfil;

    if (Object.keys(datosActualizar).length === 0) {
      return res.status(400).json({
        data: null,
        error: "No hay datos para actualizar"
      });
    }

    const { data, error } = await supabase
      .from("usuarios")
      .update(datosActualizar)
      .eq("id_usuario", id)
      .select("id_usuario, nombre, email, rol, foto_perfil")
      .single();

    if (error) {
      return res.status(500).json({
        data: null,
        error: error.message
      });
    }

    return res.json({
      data,
      error: null
    });

  } catch (error) {
    return res.status(500).json({
      data: null,
      error: error.message
    });
  }
};

// DELETE /usuarios/:id
const eliminarUsuario = async (req, res) => {
  try {
    const { id } = req.params;

    const { error } = await supabase
      .from("usuarios")
      .delete()
      .eq("id_usuario", id);

    if (error) {
      return res.status(500).json({
        data: null,
        error: error.message
      });
    }

    return res.json({
      data: "Usuario eliminado correctamente",
      error: null
    });

  } catch (error) {
    return res.status(500).json({
      data: null,
      error: error.message
    });
  }
};

// GET /usuarios/:id/tableros
const obtenerTablerosDeUsuario = async (req, res) => {
  try {
    const { id } = req.params;

    const { data, error } = await supabase
      .from("tableros")
      .select("*")
      .eq("id_usuario", id)
      .order("fecha_creacion", { ascending: false });

    if (error) {
      return res.status(500).json({
        data: null,
        error: error.message
      });
    }

    return res.json({
      data,
      error: null
    });

  } catch (error) {
    return res.status(500).json({
      data: null,
      error: error.message
    });
  }
};

// GET /usuarios/perfil/me
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

// POST /usuarios/foto-perfil
const subirFotoPerfil = async (req, res) => {
  try {
    const id_usuario = req.usuario.id_usuario;

    if (!req.file) {
      return res.status(400).json({
        data: null,
        error: "Tenés que enviar una imagen en el campo foto"
      });
    }

    let extension = req.file.originalname
      .split(".")
      .pop()
      .toLowerCase();

    if (extension === "jfif" || extension === "jpeg") {
      extension = "jpg";
    }

    const nombreArchivo = `usuario-${id_usuario}-${Date.now()}.${extension}`;
    const rutaArchivo = `${id_usuario}/${nombreArchivo}`;

    const { error: uploadError } = await supabaseAdmin.storage
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

    const { data: publicUrlData } = supabaseAdmin.storage
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