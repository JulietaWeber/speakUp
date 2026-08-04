const bcrypt = require("bcryptjs");
const jwt = require("jsonwebtoken");
const supabase = require("../config/Supabase");

const generarToken = (usuario) => {
  return jwt.sign(
    {
      id_usuario: usuario.id_usuario,
      email: usuario.email,
      rol: usuario.rol
    },
    process.env.JWT_SECRET,
    {
      expiresIn: process.env.JWT_EXPIRES_IN || "7d"
    }
  );
};

const registrarUsuario = async (req, res) => {
  try {
    const { nombre, email, password } = req.body;

    if (!nombre || !email || !password) {
      return res.status(400).json({
        data: null,
        error: "Faltan datos obligatorios"
      });
    }

    if (password.length < 6) {
      return res.status(400).json({
        data: null,
        error: "La contraseña debe tener al menos 6 caracteres"
      });
    }

    const emailNormalizado = email.trim().toLowerCase();

    const { data: usuarioExistente, error: errorBuscar } = await supabase
      .from("usuarios")
      .select("id_usuario")
      .eq("email", emailNormalizado)
      .maybeSingle();

    if (errorBuscar) {
      return res.status(500).json({
        data: null,
        error: errorBuscar.message
      });
    }

    if (usuarioExistente) {
      return res.status(400).json({
        data: null,
        error: "Ya existe un usuario con ese email"
      });
    }

    const passwordHash = await bcrypt.hash(password, 10);

    const { data: usuarioCreado, error: errorInsertar } = await supabase
      .from("usuarios")
      .insert([
        {
          nombre,
          email: emailNormalizado,
          password: passwordHash,
          rol: "usuario"
        }
      ])
      .select("id_usuario, nombre, email, rol")
      .single();

    if (errorInsertar) {
      return res.status(500).json({
        data: null,
        error: errorInsertar.message
      });
    }

    const token = generarToken(usuarioCreado);

    return res.status(201).json({
      data: {
        usuario: usuarioCreado,
        token
      },
      error: null
    });

  } catch (error) {
    return res.status(500).json({
      data: null,
      error: error.message
    });
  }
};

const loginUsuario = async (req, res) => {
  try {
    const { email, password } = req.body;

    if (!email || !password) {
      return res.status(400).json({
        data: null,
        error: "Faltan email o contraseña"
      });
    }

    const emailNormalizado = email.trim().toLowerCase();

    const { data: usuario, error: errorBuscar } = await supabase
      .from("usuarios")
      .select("id_usuario, nombre, email, password, rol")
      .eq("email", emailNormalizado)
      .maybeSingle();

    if (errorBuscar) {
      return res.status(500).json({
        data: null,
        error: errorBuscar.message
      });
    }

    if (!usuario) {
      return res.status(401).json({
        data: null,
        error: "Email o contraseña incorrectos"
      });
    }

    const passwordValida = await bcrypt.compare(password, usuario.password);

    if (!passwordValida) {
      return res.status(401).json({
        data: null,
        error: "Email o contraseña incorrectos"
      });
    }

    const usuarioSeguro = {
      id_usuario: usuario.id_usuario,
      nombre: usuario.nombre,
      email: usuario.email,
      rol: usuario.rol
    };

    const token = generarToken(usuarioSeguro);

    return res.json({
      data: {
        usuario: usuarioSeguro,
        token
      },
      error: null
    });

  } catch (error) {
    return res.status(500).json({
      data: null,
      error: error.message
    });
  }
};

const obtenerMiPerfil = async (req, res) => {
  try {
    const idUsuario = req.usuario.id_usuario;

    const { data: usuario, error } = await supabase
      .from("usuarios")
      .select("id_usuario, nombre, email, rol")
      .eq("id_usuario", idUsuario)
      .maybeSingle();

    if (error) {
      return res.status(500).json({
        data: null,
        error: error.message
      });
    }

    if (!usuario) {
      return res.status(404).json({
        data: null,
        error: "Usuario no encontrado"
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
  registrarUsuario,
  loginUsuario,
  obtenerMiPerfil
};