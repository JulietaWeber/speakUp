const bcrypt = require("bcryptjs");
const jwt = require("jsonwebtoken");
const supabase = require("../config/Supabase");
const crypto = require("crypto");

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

const generarTokenRecuperacion = () => {
  return crypto.randomBytes(32).toString("hex");
};

const hashearTokenRecuperacion = (token) => {
  return crypto
    .createHash("sha256")
    .update(token)
    .digest("hex");
};

const calcularFechaExpiracion = () => {
  const fecha = new Date();
  fecha.setMinutes(fecha.getMinutes() + 30);
  return fecha.toISOString();
};

const validarPasswordRecuperacion = (password) => {
  if (!password || password.length < 8) {
    return "La contraseña debe tener al menos 8 caracteres";
  }

  const tieneMayuscula = /[A-Z]/.test(password);
  const tieneEspecial = /[^A-Za-z0-9]/.test(password);

  if (!tieneMayuscula || !tieneEspecial) {
    return "La contraseña debe tener al menos una mayúscula y un carácter especial";
  }

  return null;
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

// POST /auth/forgot-password
const forgotPassword = async (req, res) => {
  try {
    const { email } = req.body;

    if (!email) {
      return res.status(400).json({
        data: null,
        error: "Falta el email"
      });
    }

    const emailNormalizado = String(email).trim().toLowerCase();

    const { data: usuario, error: usuarioError } = await supabase
      .from("usuarios")
      .select("id_usuario, nombre, email")
      .eq("email", emailNormalizado)
      .maybeSingle();

    if (usuarioError) {
      return res.status(500).json({
        data: null,
        error: usuarioError.message
      });
    }

    /*
      No revelamos si el email existe o no.
      Esto evita que alguien use el endpoint para descubrir usuarios registrados.
    */
    if (!usuario) {
      return res.json({
        data: {
          mensaje: "Si el email existe, se generó un token de recuperación"
        },
        error: null
      });
    }

    const token = generarTokenRecuperacion();
    const tokenHash = hashearTokenRecuperacion(token);
    const fechaExpiracion = calcularFechaExpiracion();

    // Invalidar tokens anteriores no usados del usuario
    const { error: invalidarError } = await supabase
      .from("password_reset_tokens")
      .update({ usado: true })
      .eq("id_usuario", usuario.id_usuario)
      .eq("usado", false);

    if (invalidarError) {
      return res.status(500).json({
        data: null,
        error: invalidarError.message
      });
    }

    const { error: tokenError } = await supabase
      .from("password_reset_tokens")
      .insert([
        {
          id_usuario: usuario.id_usuario,
          token_hash: tokenHash,
          usado: false,
          fecha_expiracion: fechaExpiracion
        }
      ]);

    if (tokenError) {
      return res.status(500).json({
        data: null,
        error: tokenError.message
      });
    }

    await supabase.from("historial_uso").insert([
      {
        id_usuario: usuario.id_usuario,
        accion: "solicitar_recuperacion_password",
        detalle: "Se generó un token de recuperación de contraseña"
      }
    ]);

    /*
      MVP / pruebas:
      Devolvemos el token en la respuesta para poder probar sin email.
      Después esto se reemplaza por envío de mail.
    */
    return res.json({
      data: {
        mensaje: "Token de recuperación generado correctamente",
        reset_token: token,
        expires_in_minutes: 30
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

// POST /auth/reset-password
const resetPassword = async (req, res) => {
  try {
    const {
      token,
      nueva_password
    } = req.body;

    if (!token || !nueva_password) {
      return res.status(400).json({
        data: null,
        error: "Faltan datos obligatorios: token o nueva_password"
      });
    }

    const errorPassword = validarPasswordRecuperacion(nueva_password);

    if (errorPassword) {
      return res.status(400).json({
        data: null,
        error: errorPassword
      });
    }

    const tokenHash = hashearTokenRecuperacion(token);

    const { data: resetToken, error: buscarError } = await supabase
      .from("password_reset_tokens")
      .select(`
        id_reset,
        id_usuario,
        token_hash,
        usado,
        fecha_expiracion
      `)
      .eq("token_hash", tokenHash)
      .eq("usado", false)
      .maybeSingle();

    if (buscarError) {
      return res.status(500).json({
        data: null,
        error: buscarError.message
      });
    }

    if (!resetToken) {
      return res.status(400).json({
        data: null,
        error: "Token inválido o ya utilizado"
      });
    }

    const ahora = new Date();
    const fechaExpiracion = new Date(resetToken.fecha_expiracion);

    if (fechaExpiracion < ahora) {
      await supabase
        .from("password_reset_tokens")
        .update({ usado: true })
        .eq("id_reset", resetToken.id_reset);

      return res.status(400).json({
        data: null,
        error: "El token expiró"
      });
    }

    const passwordHasheada = await bcrypt.hash(nueva_password, 10);

    const { error: updatePasswordError } = await supabase
      .from("usuarios")
      .update({
        password: passwordHasheada
      })
      .eq("id_usuario", resetToken.id_usuario);

    if (updatePasswordError) {
      return res.status(500).json({
        data: null,
        error: updatePasswordError.message
      });
    }

    const { error: marcarTokenError } = await supabase
      .from("password_reset_tokens")
      .update({ usado: true })
      .eq("id_reset", resetToken.id_reset);

    if (marcarTokenError) {
      return res.status(500).json({
        data: null,
        error: marcarTokenError.message
      });
    }

    await supabase.from("historial_uso").insert([
      {
        id_usuario: resetToken.id_usuario,
        accion: "reset_password",
        detalle: "Contraseña actualizada mediante recuperación"
      }
    ]);

    return res.json({
      data: {
        mensaje: "Contraseña actualizada correctamente"
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

module.exports = {
  registrarUsuario,
  loginUsuario,
  loginGoogle,
  obtenerMiPerfil,
  forgotPassword,
  resetPassword
};