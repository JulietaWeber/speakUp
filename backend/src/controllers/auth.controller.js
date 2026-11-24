
const bcrypt = require("bcryptjs");
const jwt = require("jsonwebtoken");
const crypto = require("node:crypto");
const supabase = require("../config/SupabaseAdmin");

const VOZ_DEFAULT = "voz_neutra";

const responderOk = (res, data, status = 200) =>
  res.status(status).json({ data, error: null });

const responderError = (res, status, error) =>
  res.status(status).json({ data: null, error });

const normalizarEmail = (email) =>
  typeof email === "string" ? email.trim().toLowerCase() : "";

const normalizarTexto = (texto) =>
  typeof texto === "string" ? texto.trim() : "";

const validarEmail = (email) =>
  /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);

const validarPasswordSegura = (password) => {
  if (typeof password !== "string" || password.length < 8) {
    return "La contraseña debe tener al menos 8 caracteres";
  }

  if (!/[A-Z]/.test(password) || !/[^A-Za-z0-9]/.test(password)) {
    return "La contraseña debe tener al menos una mayúscula y un carácter especial";
  }

  return null;
};

const armarUsuarioSeguro = (usuario) => ({
  id_usuario: usuario.id_usuario,
  nombre: usuario.nombre,
  email: usuario.email,
  rol: usuario.rol,
  foto_perfil: usuario.foto_perfil || null,
  voz_preferida: usuario.voz_preferida || VOZ_DEFAULT
});

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
      expiresIn: (process.env.JWT_EXPIRES_IN || "7d")
        .replace(/['"]/g, "")
    }
  );
};

const registrarError = (operacion, error) => {
  console.error(`[AUTH] ${operacion}:`, error?.message || error);
};

// ======================================
// REGISTRO
// POST /auth/register
// ======================================

const registrarUsuario = async (req, res) => {
  try {
    const { nombre, email, password } = req.body || {};

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

    const { data: existente, error: buscarError } = await supabase
      .from("usuarios")
      .select("id_usuario")
      .eq("email", emailNormalizado)
      .maybeSingle();

    if (buscarError) throw buscarError;

    if (existente) {
      return responderError(
        res, 409, "Ya existe un usuario con ese email"
      );
    }

    const passwordHash = await bcrypt.hash(password, 10);

    const { data: usuario, error: insertarError } = await supabase
      .from("usuarios")
      .insert({
        nombre: nombreNormalizado,
        email: emailNormalizado,
        password: passwordHash,
        rol: "usuario",
        google_id: null,
        voz_preferida: VOZ_DEFAULT
      })
      .select(
        "id_usuario, nombre, email, rol, foto_perfil, voz_preferida"
      )
      .single();

    if (insertarError) {
      if (insertarError.code === "23505") {
        return responderError(
          res, 409, "Ya existe un usuario con ese email"
        );
      }
      throw insertarError;
    }

    const usuarioSeguro = armarUsuarioSeguro(usuario);

    return responderOk(
      res,
      {
        usuario: usuarioSeguro,
        token: generarToken(usuarioSeguro)
      },
      201
    );
  } catch (error) {
    registrarError("registrarUsuario", error);
    return responderError(
      res, 500, "No se pudo registrar el usuario"
    );
  }
};

// ======================================
// LOGIN
// POST /auth/login
// ======================================

const loginUsuario = async (req, res) => {
  try {
    const { email, password } = req.body || {};

    if (!email || !password) {
      return responderError(
        res, 400, "Faltan email o contraseña"
      );
    }

    const emailNormalizado = normalizarEmail(email);

    if (!validarEmail(emailNormalizado)) {
      return responderError(
        res, 400, "El email debe tener un formato válido"
      );
    }

    const { data: usuario, error } = await supabase
      .from("usuarios")
      .select(
        "id_usuario, nombre, email, password, " +
        "rol, foto_perfil, voz_preferida, google_id"
      )
      .eq("email", emailNormalizado)
      .maybeSingle();

    if (error) throw error;

    if (!usuario) {
      return responderError(
        res, 401, "Email o contraseña incorrectos"
      );
    }

    if (!usuario.password) {
      return responderError(
        res, 401, "Este usuario debe ingresar con Google"
      );
    }

    const passwordValida = await bcrypt.compare(
      password, usuario.password
    );

    if (!passwordValida) {
      return responderError(
        res, 401, "Email o contraseña incorrectos"
      );
    }

    const usuarioSeguro = armarUsuarioSeguro(usuario);

    return responderOk(res, {
      usuario: usuarioSeguro,
      token: generarToken(usuarioSeguro)
    });
  } catch (error) {
    registrarError("loginUsuario", error);
    return responderError(
      res, 500, "No se pudo iniciar sesión"
    );
  }
};

// ======================================
// GOOGLE LOGIN
// Temporalmente deshabilitado
// ======================================

const loginGoogle = async (req, res) => {
  return responderError(
    res,
    503,
    "El inicio de sesión con Google estará disponible próximamente"
  );
};

// ======================================
// MI PERFIL
// GET /auth/me
// ======================================

const obtenerMiPerfil = async (req, res) => {
  try {
    const idUsuario = Number(req.usuario?.id_usuario);

    if (!Number.isSafeInteger(idUsuario) || idUsuario <= 0) {
      return responderError(res, 401, "Sesión inválida");
    }

    const { data: usuario, error } = await supabase
      .from("usuarios")
      .select(
        "id_usuario, nombre, email, rol, foto_perfil, voz_preferida"
      )
      .eq("id_usuario", idUsuario)
      .maybeSingle();

    if (error) throw error;

    if (!usuario) {
      return responderError(
        res, 401, "Usuario no encontrado o sesión inválida"
      );
    }

    return responderOk(res, armarUsuarioSeguro(usuario));
  } catch (error) {
    registrarError("obtenerMiPerfil", error);
    return responderError(
      res, 500, "No se pudo obtener el perfil"
    );
  }
};

// ======================================
// RECUPERACIÓN DE CONTRASEÑA
// ======================================

const hashResetToken = (token) =>
  crypto.createHash("sha256").update(token).digest("hex");

const RECUPERACION_OK =
  "Si existe una cuenta con ese correo, recibirás instrucciones para recuperar la contraseña.";

const enviarCorreoRecuperacion = async (destinatario, enlace) => {
  const apiKey = process.env.RESEND_API_KEY;

  const remitente =
    process.env.RESEND_FROM_EMAIL ||
    "SpeakUP <onboarding@resend.dev>";

  if (!apiKey) {
    throw new Error("RESEND_API_KEY no está configurada");
  }

  const respuesta = await fetch("https://api.resend.com/emails", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${apiKey}`,
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      from: remitente,
      to: [destinatario],
      subject: "Recuperá tu contraseña de SpeakUP",
      html: `
        <div style="font-family:Arial,sans-serif;max-width:520px;margin:auto">
          <h2>SpeakUP</h2>
          <p>Recibimos una solicitud para cambiar tu contraseña.</p>
          <p>
            <a href="${enlace}"
               style="display:inline-block;padding:12px 18px;background:#29334a;color:#fff;text-decoration:none;border-radius:6px">
              Restablecer contraseña
            </a>
          </p>
          <p>El enlace vence en 15 minutos y se puede usar una sola vez.</p>
          <p>Si no pediste este cambio, ignorá el mensaje.</p>
        </div>
      `
    })
  });

  if (!respuesta.ok) {
    let detalle = "";

    try {
      const json = await respuesta.json();
      detalle = json.message || json.name || "";
    } catch (_) {
      // No mostrar tokens ni claves.
    }

    throw new Error(
      `Resend devolvió HTTP ${respuesta.status}: ${detalle}`
    );
  }
};

// ======================================
// OLVIDÉ MI CONTRASEÑA
// POST /auth/forgot-password
// Body: { email }
// ======================================

const forgotPassword = async (req, res) => {
  try {
    const email = normalizarEmail(req.body?.email);

    if (!validarEmail(email)) {
      return responderError(
        res, 400, "Ingresá un correo válido"
      );
    }

    const { data: usuario, error: buscarError } = await supabase
      .from("usuarios")
      .select("id_usuario, email, password")
      .eq("email", email)
      .maybeSingle();

    if (buscarError) throw buscarError;

    // No revelar si el correo está registrado.
    if (!usuario || !usuario.password) {
      return responderOk(res, { mensaje: RECUPERACION_OK });
    }

    // Evitar solicitudes repetidas para la misma cuenta.
    const desde = new Date(
      Date.now() - 2 * 60 * 1000
    ).toISOString();

    const { data: reciente, error: recienteError } = await supabase
      .from("password_reset_tokens")
      .select("id_reset")
      .eq("id_usuario", usuario.id_usuario)
      .gte("fecha_creacion", desde)
      .limit(1);

    if (recienteError) throw recienteError;

    if (reciente?.length) {
      return responderOk(res, { mensaje: RECUPERACION_OK });
    }

    const base = process.env.APP_PUBLIC_URL;

    if (!base || !/^https:\/\/[^\s]+$/i.test(base)) {
      throw new Error(
        "APP_PUBLIC_URL debe ser una URL HTTPS pública del backend"
      );
    }

    const token = crypto.randomBytes(32).toString("hex");
    const tokenHash = hashResetToken(token);

    const expiracion = new Date(
      Date.now() + 15 * 60 * 1000
    ).toISOString();

    const { data: creado, error: guardarError } = await supabase
      .from("password_reset_tokens")
      .insert({
        id_usuario: usuario.id_usuario,
        token_hash: tokenHash,
        usado: false,
        fecha_expiracion: expiracion
      })
      .select("id_reset")
      .single();

    if (guardarError) throw guardarError;

    const enlace =
      `${base.replace(/\/$/, "")}` +
      `/auth/reset-password-page#token=${token}`;

    try {
      await enviarCorreoRecuperacion(usuario.email, enlace);
    } catch (correoError) {
      registrarError("envío recuperación", correoError);

      await supabase
        .from("password_reset_tokens")
        .delete()
        .eq("id_reset", creado.id_reset);
    }

    return responderOk(res, {
      mensaje: RECUPERACION_OK
    });
  } catch (error) {
    registrarError("forgotPassword", error);

    return responderError(
      res, 500, "No pudimos procesar la solicitud"
    );
  }
};

// ======================================
// RESTABLECER CONTRASEÑA
// POST /auth/reset-password
// Body: { token, newPassword }
// ======================================

const resetPassword = async (req, res) => {
  try {
    const token = req.body?.token;

    const nueva =
      req.body?.newPassword ??
      req.body?.nuevaPassword;

    if (
      typeof token !== "string" ||
      !/^[a-f0-9]{64}$/i.test(token)
    ) {
      return responderError(
        res, 400, "Enlace inválido o vencido"
      );
    }

    const errorPassword = validarPasswordSegura(nueva);

    if (errorPassword) {
      return responderError(res, 400, errorPassword);
    }

    const { data: registro, error: buscarError } = await supabase
      .from("password_reset_tokens")
      .select("id_reset, id_usuario")
      .eq("token_hash", hashResetToken(token))
      .eq("usado", false)
      .gt("fecha_expiracion", new Date().toISOString())
      .maybeSingle();

    if (buscarError) throw buscarError;

    if (!registro) {
      return responderError(
        res, 400, "Enlace inválido o vencido"
      );
    }

    // Reclamar el token para impedir su reutilización.
    const { data: reclamado, error: marcarError } = await supabase
      .from("password_reset_tokens")
      .update({ usado: true })
      .eq("id_reset", registro.id_reset)
      .eq("usado", false)
      .gt("fecha_expiracion", new Date().toISOString())
      .select("id_reset")
      .maybeSingle();

    if (marcarError) throw marcarError;

    if (!reclamado) {
      return responderError(
        res, 400, "Enlace ya utilizado o vencido"
      );
    }

    const passwordHash = await bcrypt.hash(nueva, 10);

    const { data: actualizado, error: passwordError } =
      await supabase
        .from("usuarios")
        .update({ password: passwordHash })
        .eq("id_usuario", registro.id_usuario)
        .select("id_usuario")
        .maybeSingle();

    if (passwordError || !actualizado) {
      throw passwordError || new Error("Usuario no encontrado");
    }

    // Invalidar otros enlaces pendientes.
    const { error: invalidarError } = await supabase
      .from("password_reset_tokens")
      .update({ usado: true })
      .eq("id_usuario", registro.id_usuario)
      .eq("usado", false);

    if (invalidarError) {
      registrarError("invalidar enlaces", invalidarError);
    }

    return responderOk(res, {
      mensaje: "Contraseña actualizada correctamente"
    });
  } catch (error) {
    registrarError("resetPassword", error);

    return responderError(
      res, 500, "No se pudo actualizar la contraseña"
    );
  }
};

// ======================================
// CAMBIAR CONTRASEÑA CON SESIÓN INICIADA
// PUT /auth/change-password
// Body: { currentPassword, newPassword }
// ======================================

const changePassword = async (req, res) => {
  try {
    const idUsuario = Number(req.usuario?.id_usuario);

    if (!Number.isSafeInteger(idUsuario) || idUsuario <= 0) {
      return responderError(res, 401, "Sesión inválida");
    }

    const actual =
      req.body?.currentPassword ??
      req.body?.passwordActual;

    const nueva =
      req.body?.newPassword ??
      req.body?.nuevaPassword;

    if (typeof actual !== "string" || !actual) {
      return responderError(
        res, 400, "Ingresá la contraseña actual"
      );
    }

    const errorPassword = validarPasswordSegura(nueva);

    if (errorPassword) {
      return responderError(res, 400, errorPassword);
    }

    const { data: usuario, error: buscarError } = await supabase
      .from("usuarios")
      .select("id_usuario, password")
      .eq("id_usuario", idUsuario)
      .maybeSingle();

    if (buscarError) throw buscarError;

    if (
      !usuario?.password ||
      !(await bcrypt.compare(actual, usuario.password))
    ) {
      return responderError(
        res, 401, "Contraseña actual incorrecta"
      );
    }

    if (await bcrypt.compare(nueva, usuario.password)) {
      return responderError(
        res, 400, "La nueva contraseña debe ser diferente"
      );
    }

    const nuevoHash = await bcrypt.hash(nueva, 10);

    const { data: actualizado, error: actualizarError } =
      await supabase
        .from("usuarios")
        .update({ password: nuevoHash })
        .eq("id_usuario", idUsuario)
        .eq("password", usuario.password)
        .select("id_usuario")
        .maybeSingle();

    if (actualizarError) throw actualizarError;

    if (!actualizado) {
      return responderError(
        res, 409, "Volvé a intentar el cambio"
      );
    }

    const { error: invalidarError } = await supabase
      .from("password_reset_tokens")
      .update({ usado: true })
      .eq("id_usuario", idUsuario)
      .eq("usado", false);

    if (invalidarError) {
      registrarError("invalidar enlaces", invalidarError);
    }

    return responderOk(res, {
      mensaje: "Contraseña modificada correctamente"
    });
  } catch (error) {
    registrarError("changePassword", error);

    return responderError(
      res, 500, "No se pudo cambiar la contraseña"
    );
  }
};

// ======================================
// PÁGINA WEB PARA RESTABLECER CONTRASEÑA
// GET /auth/reset-password-page
// ======================================

const resetPasswordPage = (req, res) => {
  res.set("Cache-Control", "no-store");
  res.set("Referrer-Policy", "no-referrer");
  res.set("X-Content-Type-Options", "nosniff");

  res.type("html").send(`<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Restablecer contraseña | SpeakUP</title>
<style>
body {
  font-family: system-ui, sans-serif;
  background: #f4f5f7;
  margin: 0;
  padding: 24px;
  color: #20242c;
}
main {
  max-width: 430px;
  margin: 12vh auto;
  background: white;
  border-radius: 14px;
  padding: 28px;
  box-shadow: 0 8px 28px #0001;
}
h1 { margin: 0 0 18px; }
input, button {
  box-sizing: border-box;
  width: 100%;
  padding: 13px;
  margin: 8px 0;
  border-radius: 8px;
  font-size: 16px;
}
input { border: 1px solid #bbb; }
button {
  border: 0;
  background: #29334a;
  color: white;
  cursor: pointer;
}
p { line-height: 1.5; }
</style>
</head>
<body>
<main>
  <h1>SpeakUP</h1>
  <p>Elegí una contraseña nueva (mínimo 8 caracteres, una mayúscula y un carácter especial).</p>
  <form id="form">
    <input id="pass" type="password" autocomplete="new-password"
      placeholder="Nueva contraseña" required minlength="8">
    <input id="confirm" type="password" autocomplete="new-password"
      placeholder="Repetir contraseña" required minlength="8">
    <button type="submit">Guardar contraseña</button>
  </form>
  <p id="mensaje" role="status"></p>
</main>
<script>
const params = new URLSearchParams(location.hash.slice(1));
const token = params.get('token');
history.replaceState(null, '', location.pathname);

const msg = document.getElementById('mensaje');

if (!token) {
  msg.textContent = 'Enlace inválido. Solicitá uno nuevo.';
  document.getElementById('form').style.display = 'none';
}

document.getElementById('form').addEventListener('submit', async (event) => {
  event.preventDefault();

  const nueva = document.getElementById('pass').value;
  const confirmacion = document.getElementById('confirm').value;

  if (nueva !== confirmacion) {
    msg.textContent = 'Las contraseñas no coinciden';
    return;
  }

  msg.textContent = 'Guardando...';

  try {
    const respuesta = await fetch('/auth/reset-password', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ token, newPassword: nueva })
    });

    const json = await respuesta.json();

    if (!respuesta.ok) {
      throw new Error(
        json.error || 'No se pudo cambiar la contraseña'
      );
    }

    msg.textContent =
      'Contraseña actualizada. Ya podés iniciar sesión en SpeakUP.';

    document.getElementById('form').style.display = 'none';
  } catch (error) {
    msg.textContent = error.message;
  }
});
</script>
</body>
</html>`);
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
  resetPassword,
  resetPasswordPage,
  changePassword
};
