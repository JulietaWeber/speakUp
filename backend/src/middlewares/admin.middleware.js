
const supabaseAdmin = require("../config/SupabaseAdmin");

const verificarAdmin = async (req, res, next) => {
  try {
    // Primero debe existir un usuario autenticado.
    if (!req.usuario?.id_usuario) {
      return res.status(401).json({
        data: null,
        error: "Usuario no autenticado"
      });
    }

    const id_usuario = Number(req.usuario.id_usuario);

    if (
      !Number.isSafeInteger(id_usuario) ||
      id_usuario <= 0
    ) {
      return res.status(401).json({
        data: null,
        error: "Sesión inválida"
      });
    }

    // Consultar el rol actualizado en la base de datos.
    const { data: usuario, error } = await supabaseAdmin
      .from("usuarios")
      .select("id_usuario, rol")
      .eq("id_usuario", id_usuario)
      .maybeSingle();

    if (error) {
      console.error("Error verificando administrador:", error);

      return res.status(500).json({
        data: null,
        error: "No se pudieron verificar los permisos"
      });
    }

    if (!usuario) {
      return res.status(401).json({
        data: null,
        error: "Usuario no encontrado o sesión inválida"
      });
    }

    if (usuario.rol !== "admin") {
      return res.status(403).json({
        data: null,
        error: "Acceso denegado: se requiere rol admin"
      });
    }

    // Actualizar el rol para los siguientes middlewares.
    req.usuario.rol = usuario.rol;

    return next();

  } catch (error) {
    console.error("Error en verificarAdmin:", error);

    return res.status(500).json({
      data: null,
      error: "Error interno verificando permisos"
    });
  }
};

module.exports = verificarAdmin;
