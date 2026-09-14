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
      expiresIn: (process.env.JWT_EXPIRES_IN || "7d").replace(/['"]/g, "")
    }
  );
};

const validarEmail = (email) => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
};

const validarPasswordRegistro = (password) => {
  const tieneMinimo8 = password.length >= 8;
  const tieneMayuscula = /[A-Z]/.test(password);
  const tieneCaracterEspecial = /[^A-Za-z0-9]/.test(password);

  return tieneMinimo8 && tieneMayuscula && tieneCaracterEspecial;
};

const armarUsuarioSeguro = (usuario) => {
  return {
    id_usuario: usuario.id_usuario,
    nombre: usuario.nombre,
    email: usuario.email,
    rol: usuario.rol,
    foto_perfil: usuario.foto_perfil || null
  };
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

    const nombreNormalizado = nombre.trim();
    const emailNormalizado = email.trim().toLowerCase();

    if (!nombreNormalizado) {
      return res.status(400).json({
        data: null,
        error: "El nombre no puede estar vacío"
      });
    }

    if (!validarEmail(emailNormalizado)) {
      return res.status(400).json({
        data: null,
        error: "El email debe tener un formato válido"
      });
    }

    if (!validarPasswordRegistro(password)) {
      return res.status(400).json({
        data: null,
        error: "La contraseña debe tener al menos 8 caracteres, una mayúscula y un carácter especial"
      });
    }

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
          nombre: nombreNormalizado,
          email: emailNormalizado,
          password: passwordHash,
          rol: "usuario",
          google_id: null
        }
      ])
      .select("id_usuario, nombre, email, rol, foto_perfil, google_id")
      .single();

    if (errorInsertar) {
      return res.status(500).json({
        data: null,
        error: errorInsertar.message
      });
    }

    const usuarioSeguro = armarUsuarioSeguro(usuarioCreado);
    const token = generarToken(usuarioSeguro);

    return res.status(201).json({
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

    if (!validarEmail(emailNormalizado)) {
      return res.status(400).json({
        data: null,
        error: "El email debe tener un formato válido"
      });
    }

    const { data: usuario, error: errorBuscar } = await supabase
      .from("usuarios")
      .select("id_usuario, nombre, email, password, rol, foto_perfil")
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

    if (!usuario.password) {
      return res.status(401).json({
        data: null,
        error: "Este usuario debe ingresar con Google"
      });
    }

    const passwordValida = await bcrypt.compare(password, usuario.password);

    if (!passwordValida) {
      return res.status(401).json({
        data: null,
        error: "Email o contraseña incorrectos"
      });
    }

    const usuarioSeguro = armarUsuarioSeguro(usuario);
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

const loginGoogle = async (req, res) => {
  try {
    const { nombre, email, google_id } = req.body;

    if (!email || !google_id) {
      return res.status(400).json({
        data: null,
        error: "Faltan datos obligatorios: email y google_id"
      });
    }

    const emailNormalizado = email.trim().toLowerCase();
    const nombreNormalizado = nombre ? nombre.trim() : "Usuario Google";

    if (!validarEmail(emailNormalizado)) {
      return res.status(400).json({
        data: null,
        error: "El email debe tener un formato válido"
      });
    }

    const { data: usuarioExistente, error: errorBuscar } = await supabase
      .from("usuarios")
      .select("id_usuario, nombre, email, rol, foto_perfil, google_id")
      .eq("email", emailNormalizado)
      .maybeSingle();

    if (errorBuscar) {
      return res.status(500).json({
        data: null,
        error: errorBuscar.message
      });
    }

    if (usuarioExistente) {
      const camposActualizar = {};

      if (!usuarioExistente.google_id) {
        camposActualizar.google_id = google_id;
      }

      if (!usuarioExistente.nombre && nombreNormalizado) {
        camposActualizar.nombre = nombreNormalizado;
      }

      let usuarioFinal = usuarioExistente;

      if (Object.keys(camposActualizar).length > 0) {
        const { data: usuarioActualizado, error: errorActualizar } = await supabase
          .from("usuarios")
          .update(camposActualizar)
          .eq("id_usuario", usuarioExistente.id_usuario)
          .select("id_usuario, nombre, email, rol, foto_perfil, google_id")
          .single();

        if (errorActualizar) {
          return res.status(500).json({
            data: null,
            error: errorActualizar.message
          });
        }

        usuarioFinal = usuarioActualizado;
      }

      const usuarioSeguro = armarUsuarioSeguro(usuarioFinal);
      const token = generarToken(usuarioSeguro);

      return res.json({
        data: {
          usuario: usuarioSeguro,
          token
        },
        error: null
      });
    }

    const passwordTemporal = await bcrypt.hash(
      `google-${google_id}-${Date.now()}`,
      10
    );

    const { data: usuarioCreado, error: errorInsertar } = await supabase
      .from("usuarios")
      .insert([
        {
          nombre: nombreNormalizado,
          email: emailNormalizado,
          password: passwordTemporal,
          rol: "usuario",
          google_id
        }
      ])
      .select("id_usuario, nombre, email, rol, foto_perfil, google_id")
      .single();

    if (errorInsertar) {
      return res.status(500).json({
        data: null,
        error: errorInsertar.message
      });
    }

    const usuarioSeguro = armarUsuarioSeguro(usuarioCreado);
    const token = generarToken(usuarioSeguro);

    return res.status(201).json({
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
      .select("id_usuario, nombre, email, rol, foto_perfil, google_id")
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
      data: armarUsuarioSeguro(usuario),
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
  loginGoogle,
  obtenerMiPerfil
};