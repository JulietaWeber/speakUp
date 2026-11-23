
const bcrypt = require("bcryptjs");
const jwt = require("jsonwebtoken");

const supabase = require("../config/SupabaseAdmin");

const VOZ_DEFAULT = "voz_neutra";

// ======================================
// HELPERS GENERALES
// ======================================

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
  return typeof email === "string"
    ? email.trim().toLowerCase()
    : "";
};

const normalizarTexto = (texto) => {
  return typeof texto === "string"
    ? texto.trim()
    : "";
};

const validarEmail = (email) => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
};

const validarPasswordSegura = (password) => {
  if (typeof password !== "string" || password.length < 8) {
    return "La contraseña debe tener al menos 8 caracteres";
  }

  const tieneMayuscula = /[A-Z]/.test(password);
  const tieneCaracterEspecial = /[^A-Za-z0-9]/.test(password);

  if (!tieneMayuscula || !tieneCaracterEspecial) {
    return (
      "La contraseña debe tener al menos una mayúscula " +
      "y un carácter especial"
    );
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

const generarToken = (usuario) => {
  if (!process.env.JWT_SECRET) {
    throw new Error("JWT_SECRET no está configurado");
  }

  return jwt.sign(
    {
      id_usuario: usuario.id_usuario,
      email: usuario.email,
      rol: usuario.rol
    },
    process.env.JWT_SECRET,
    {
      expiresIn: (
        process.env.JWT_EXPIRES_IN || "7d"
      ).replace(/['"]/g, "")
    }
  );
};

const registrarError = (operacion, error) => {
  console.error(
    `[AUTH] ${operacion}:`,
    error?.message || error
  );
};

// ======================================
// POST /auth/register
// ======================================

const registrarUsuario = async (req, res) => {
  try {
    const { nombre, email, password } = req.body || {};

    if (!nombre || !email || !password) {
      return responderError(
        res,
        400,
        "Faltan datos obligatorios"
      );
    }

    const nombreNormalizado = normalizarTexto(nombre);
    const emailNormalizado = normalizarEmail(email);

    if (!nombreNormalizado) {
      return responderError(
        res,
        400,
        "El nombre no puede estar vacío"
      );
    }

    if (!validarEmail(emailNormalizado)) {
      return responderError(
        res,
        400,
        "El email debe tener un formato válido"
      );
    }

    const errorPassword = validarPasswordSegura(password);

    if (errorPassword) {
      return responderError(res, 400, errorPassword);
    }

    // Verificar si existe el usuario.
    const {
      data: usuarioExistente,
      error: errorBuscar
    } = await supabase
      .from("usuarios")
      .select("id_usuario")
      .eq("email", emailNormalizado)
      .maybeSingle();

    if (errorBuscar) {
      registrarError("register - buscar", errorBuscar);

      return responderError(
        res,
        500,
        "No se pudo registrar el usuario"
      );
    }

    if (usuarioExistente) {
      return responderError(
        res,
        409,
        "Ya existe un usuario con ese email"
      );
    }

    const passwordHash = await bcrypt.hash(password, 10);

    const {
      data: usuarioCreado,
      error: errorInsertar
    } = await supabase
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
      .select(
        "id_usuario, nombre, email, rol, " +
        "foto_perfil, voz_preferida"
      )
      .single();

    if (errorInsertar) {
      registrarError("register - insertar", errorInsertar);

      if (errorInsertar.code === "23505") {
        return responderError(
          res,
          409,
          "Ya existe un usuario con ese email"
        );
      }

      return responderError(
        res,
        500,
        "No se pudo registrar el usuario"
      );
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
    registrarError("registrarUsuario", error);

    return responderError(
      res,
      500,
      "No se pudo registrar el usuario"
    );
  }
};

// ======================================
// POST /auth/login
// ======================================

const loginUsuario = async (req, res) => {
  try {
    const { email, password } = req.body || {};

    if (!email || !password) {
      return responderError(
        res,
        400,
        "Faltan email o contraseña"
      );
    }

    const emailNormalizado = normalizarEmail(email);

    if (!validarEmail(emailNormalizado)) {
      return responderError(
        res,
        400,
        "El email debe tener un formato válido"
      );
    }

    const {
      data: usuario,
      error: errorBuscar
    } = await supabase
      .from("usuarios")
      .select(
        "id_usuario, nombre, email, password, " +
        "rol, foto_perfil, voz_preferida, google_id"
      )
      .eq("email", emailNormalizado)
      .maybeSingle();

    if (errorBuscar) {
      registrarError("login - buscar", errorBuscar);

      return responderError(
        res,
        500,
        "No se pudo iniciar sesión"
      );
    }

    if (!usuario) {
      return responderError(
        res,
        401,
        "Email o contraseña incorrectos"
      );
    }

    if (!usuario.password) {
      return responderError(
        res,
        401,
        "Este usuario debe ingresar con Google"
      );
    }

    const passwordValida = await bcrypt.compare(
      password,
      usuario.password
    );

    if (!passwordValida) {
      return responderError(
        res,
        401,
        "Email o contraseña incorrectos"
      );
    }

    const usuarioSeguro = armarUsuarioSeguro(usuario);
    const token = generarToken(usuarioSeguro);

    return responderOk(res, {
      usuario: usuarioSeguro,
      token
    });

  } catch (error) {
    registrarError("loginUsuario", error);

    return responderError(
      res,
      500,
      "No se pudo iniciar sesión"
    );
  }
};

// ======================================
// POST /auth/google
// ======================================

// Temporalmente deshabilitado.
// Antes de habilitarlo, el backend debe verificar
// un ID token auténtico emitido por Google.
// No se debe confiar solamente en email o google_id
// enviados desde el frontend.

const loginGoogle = async (req, res) => {
  return responderError(
    res,
    503,
    "El inicio de sesión con Google estará disponible próximamente"
  );
};

// ======================================
// GET /auth/me
// ======================================

const obtenerMiPerfil = async (req, res) => {
  try {
    const idUsuario = req.usuario?.id_usuario;

    if (
      !Number.isSafeInteger(Number(idUsuario)) ||
      Number(idUsuario) <= 0
    ) {
      return responderError(
        res,
        401,
        "Sesión inválida"
      );
    }

    const {
      data: usuario,
      error
    } = await supabase
      .from("usuarios")
      .select(
        "id_usuario, nombre, email, rol, " +
        "foto_perfil, voz_preferida"
      )
      .eq("id_usuario", idUsuario)
      .maybeSingle();

    if (error) {
      registrarError("obtenerMiPerfil", error);

      return responderError(
        res,
        500,
        "No se pudo obtener el perfil"
      );
    }

    if (!usuario) {
      return responderError(
        res,
        401,
        "Usuario no encontrado o sesión inválida"
      );
    }

    return responderOk(
      res,
      armarUsuarioSeguro(usuario)
    );

  } catch (error) {
    registrarError("obtenerMiPerfil", error);

    return responderError(
      res,
      500,
      "No se pudo obtener el perfil"
    );
  }
};

// ======================================
// POST /auth/forgot-password
// ======================================

// Temporalmente deshabilitado.
// El flujo definitivo debe generar un token
// aleatorio, guardar su hash y enviar el token
// únicamente al email verificado del usuario.
// Nunca devolver reset_token en la respuesta.

const forgotPassword = async (req, res) => {
  return responderError(
    res,
    503,
    "La recuperación de contraseña estará disponible próximamente"
  );
};

// ======================================
// POST /auth/reset-password
// ======================================

// Temporalmente deshabilitado hasta integrar
// el flujo seguro de recuperación por correo.

const resetPassword = async (req, res) => {
  return responderError(
    res,
    503,
    "La recuperación de contraseña estará disponible próximamente"
  );
};

// ======================================
// EXPORTACIONES
// ======================================

module.exports = {
  registrarUsuario,
  loginUsuario,
  loginGoogle,
  obtenerMiPerfil,
  forgotPassword,
  resetPassword
};
