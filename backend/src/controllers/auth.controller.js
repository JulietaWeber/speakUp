const bcrypt = require("bcryptjs");
const jwt = require("jsonwebtoken");
const crypto = require("crypto");

const supabase = require("../config/Supabase");

const VOZ_DEFAULT = "voz_neutra";

// =====================
// Helpers generales
// =====================

const responderOk = (res, data, status = 200) => {
  return res.status(status).json({
    data,
    error: null
  });
};

const responderError = (res, status, error) => {
  return res.status(status).json({
    data: null,
    error
  });
};

const normalizarEmail = (email) => {
  return String(email || "").trim().toLowerCase();
};

const normalizarTexto = (texto) => {
  return String(texto || "").trim();
};

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

const validarPasswordSegura = (password) => {
  if (!password || password.length < 8) {
    return "La contraseña debe tener al menos 8 caracteres";
  }

  const tieneMayuscula = /[A-Z]/.test(password);
  const tieneCaracterEspecial = /[^A-Za-z0-9]/.test(password);

  if (!tieneMayuscula || !tieneCaracterEspecial) {
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
    foto_perfil: usuario.foto_perfil || null,
    voz_preferida: usuario.voz_preferida || VOZ_DEFAULT
  };
};

// =====================
// Helpers recuperación
// =====================

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

// =====================
// POST /auth/register
// =====================

const registrarUsuario = async (req, res) => {
  try {
    const { nombre, email, password } = req.body;

    if (!nombre || !email || !password) {
      return responderError(res, 400, "Faltan datos obligatorios");
    }

    const nombreNormalizado = normalizarTexto(nombre);
    const emailNormalizado = normalizarEmail(email);

    if (!nombreNormalizado) {
      return responderError(res, 400, "El nombre no puede estar vacío");
    }

    if (!validarEmail(emailNormalizado)) {
      return responderError(res, 400, "El email debe tener un formato válido");
    }

    const errorPassword = validarPasswordSegura(password);

    if (errorPassword) {
      return responderError(res, 400, errorPassword);
    }

    const { data: usuarioExistente, error: errorBuscar } = await supabase
      .from("usuarios")
      .select("id_usuario")
      .eq("email", emailNormalizado)
      .maybeSingle();

    if (errorBuscar) {
      return responderError(res, 500, errorBuscar.message);
    }

    if (usuarioExistente) {
      return responderError(res, 400, "Ya existe un usuario con ese email");
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
          google_id: null,
          voz_preferida: VOZ_DEFAULT
        }
      ])
      .select("id_usuario, nombre, email, rol, foto_perfil, google_id, voz_preferida")
      .single();

    if (errorInsertar) {
      return responderError(res, 500, errorInsertar.message);
    }

    const usuarioSeguro = armarUsuarioSeguro(usuarioCreado);
    const token = generarToken(usuarioSeguro);

    return responderOk(
      res,
      {
        usuario: usuarioSeguro,
        token
      },
      201
    );

  } catch (error) {
    return responderError(res, 500, error.message);
  }
};

// =====================
// POST /auth/login
// =====================

const loginUsuario = async (req, res) => {
  try {
    const { email, password } = req.body;

    if (!email || !password) {
      return responderError(res, 400, "Faltan email o contraseña");
    }

    const emailNormalizado = normalizarEmail(email);

    if (!validarEmail(emailNormalizado)) {
      return responderError(res, 400, "El email debe tener un formato válido");
    }

    const { data: usuario, error: errorBuscar } = await supabase
      .from("usuarios")
      .select("id_usuario, nombre, email, password, rol, foto_perfil, voz_preferida")
      .eq("email", emailNormalizado)
      .maybeSingle();

    if (errorBuscar) {
      return responderError(res, 500, errorBuscar.message);
    }

    if (!usuario) {
      return responderError(res, 401, "Email o contraseña incorrectos");
    }

    if (!usuario.password) {
      return responderError(res, 401, "Este usuario debe ingresar con Google");
    }

    const passwordValida = await bcrypt.compare(password, usuario.password);

    if (!passwordValida) {
      return responderError(res, 401, "Email o contraseña incorrectos");
    }

    const usuarioSeguro = armarUsuarioSeguro(usuario);
    const token = generarToken(usuarioSeguro);

    return responderOk(res, {
      usuario: usuarioSeguro,
      token
    });

  } catch (error) {
    return responderError(res, 500, error.message);
  }
};

// =====================
// POST /auth/google
// =====================

const loginGoogle = async (req, res) => {
  try {
    const { nombre, email, google_id } = req.body;

    if (!email || !google_id) {
      return responderError(res, 400, "Faltan datos obligatorios: email y google_id");
    }

    const emailNormalizado = normalizarEmail(email);
    const nombreNormalizado = nombre ? normalizarTexto(nombre) : "Usuario Google";

    if (!validarEmail(emailNormalizado)) {
      return responderError(res, 400, "El email debe tener un formato válido");
    }

    const { data: usuarioExistente, error: errorBuscar } = await supabase
      .from("usuarios")
      .select("id_usuario, nombre, email, rol, foto_perfil, google_id, voz_preferida")
      .eq("email", emailNormalizado)
      .maybeSingle();

    if (errorBuscar) {
      return responderError(res, 500, errorBuscar.message);
    }

    if (usuarioExistente) {
      const camposActualizar = {};

      if (!usuarioExistente.google_id) {
        camposActualizar.google_id = google_id;
      }

      if (!usuarioExistente.nombre && nombreNormalizado) {
        camposActualizar.nombre = nombreNormalizado;
      }

      if (!usuarioExistente.voz_preferida) {
        camposActualizar.voz_preferida = VOZ_DEFAULT;
      }

      let usuarioFinal = usuarioExistente;

      if (Object.keys(camposActualizar).length > 0) {
        const { data: usuarioActualizado, error: errorActualizar } = await supabase
          .from("usuarios")
          .update(camposActualizar)
          .eq("id_usuario", usuarioExistente.id_usuario)
          .select("id_usuario, nombre, email, rol, foto_perfil, google_id, voz_preferida")
          .single();

        if (errorActualizar) {
          return responderError(res, 500, errorActualizar.message);
        }

        usuarioFinal = usuarioActualizado;
      }

      const usuarioSeguro = armarUsuarioSeguro(usuarioFinal);
      const token = generarToken(usuarioSeguro);

      return responderOk(res, {
        usuario: usuarioSeguro,
        token
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
          google_id,
          voz_preferida: VOZ_DEFAULT
        }
      ])
      .select("id_usuario, nombre, email, rol, foto_perfil, google_id, voz_preferida")
      .single();

    if (errorInsertar) {
      return responderError(res, 500, errorInsertar.message);
    }

    const usuarioSeguro = armarUsuarioSeguro(usuarioCreado);
    const token = generarToken(usuarioSeguro);

    return responderOk(
      res,
      {
        usuario: usuarioSeguro,
        token
      },
      201
    );

  } catch (error) {
    return responderError(res, 500, error.message);
  }
};

// =====================
// GET /auth/me
// =====================

const obtenerMiPerfil = async (req, res) => {
  try {
    const idUsuario = req.usuario.id_usuario;

    const { data: usuario, error } = await supabase
      .from("usuarios")
      .select("id_usuario, nombre, email, rol, foto_perfil, google_id, voz_preferida")
      .eq("id_usuario", idUsuario)
      .maybeSingle();

    if (error) {
      return responderError(res, 500, error.message);
    }

    if (!usuario) {
      return responderError(res, 404, "Usuario no encontrado");
    }

    return responderOk(res, armarUsuarioSeguro(usuario));

  } catch (error) {
    return responderError(res, 500, error.message);
  }
};

// =====================
// POST /auth/forgot-password
// =====================

const forgotPassword = async (req, res) => {
  try {
    const { email } = req.body;

    if (!email) {
      return responderError(res, 400, "Falta el email");
    }

    const emailNormalizado = normalizarEmail(email);

    if (!validarEmail(emailNormalizado)) {
      return responderError(res, 400, "El email debe tener un formato válido");
    }

    const { data: usuario, error: usuarioError } = await supabase
      .from("usuarios")
      .select("id_usuario, nombre, email")
      .ilike("email", emailNormalizado)
      .maybeSingle();

    if (usuarioError) {
      return responderError(res, 500, usuarioError.message);
    }

    /*
      No revelamos si el email existe o no.
      Esto evita que alguien use el endpoint para descubrir usuarios registrados.
    */
    if (!usuario) {
      return responderOk(res, {
        mensaje: "Si el email existe, se generó un token de recuperación"
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
      return responderError(res, 500, invalidarError.message);
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
      return responderError(res, 500, tokenError.message);
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
    return responderOk(res, {
      mensaje: "Token de recuperación generado correctamente",
      reset_token: token,
      expires_in_minutes: 30
    });

  } catch (error) {
    return responderError(res, 500, error.message);
  }
};

// =====================
// POST /auth/reset-password
// =====================

const resetPassword = async (req, res) => {
  try {
    const {
      token,
      nueva_password
    } = req.body;

    if (!token || !nueva_password) {
      return responderError(res, 400, "Faltan datos obligatorios: token o nueva_password");
    }

    const errorPassword = validarPasswordSegura(nueva_password);

    if (errorPassword) {
      return responderError(res, 400, errorPassword);
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
      return responderError(res, 500, buscarError.message);
    }

    if (!resetToken) {
      return responderError(res, 400, "Token inválido o ya utilizado");
    }

    const ahora = new Date();
    const fechaExpiracion = new Date(resetToken.fecha_expiracion);

    if (fechaExpiracion < ahora) {
      await supabase
        .from("password_reset_tokens")
        .update({ usado: true })
        .eq("id_reset", resetToken.id_reset);

      return responderError(res, 400, "El token expiró");
    }

    const passwordHasheada = await bcrypt.hash(nueva_password, 10);

    const { error: updatePasswordError } = await supabase
      .from("usuarios")
      .update({
        password: passwordHasheada
      })
      .eq("id_usuario", resetToken.id_usuario);

    if (updatePasswordError) {
      return responderError(res, 500, updatePasswordError.message);
    }

    const { error: marcarTokenError } = await supabase
      .from("password_reset_tokens")
      .update({ usado: true })
      .eq("id_reset", resetToken.id_reset);

    if (marcarTokenError) {
      return responderError(res, 500, marcarTokenError.message);
    }

    await supabase.from("historial_uso").insert([
      {
        id_usuario: resetToken.id_usuario,
        accion: "reset_password",
        detalle: "Contraseña actualizada mediante recuperación"
      }
    ]);

    return responderOk(res, {
      mensaje: "Contraseña actualizada correctamente"
    });

  } catch (error) {
    return responderError(res, 500, error.message);
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