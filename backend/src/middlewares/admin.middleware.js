const verificarAdmin = (req, res, next) => {
  try {
    if (!req.usuario) {
      return res.status(401).json({
        data: null,
        error: "Usuario no autenticado"
      });
    }

    if (req.usuario.rol !== "admin") {
      return res.status(403).json({
        data: null,
        error: "Acceso denegado: se requiere rol admin"
      });
    }

    next();

  } catch (error) {
    return res.status(500).json({
      data: null,
      error: error.message
    });
  }
};

module.exports = verificarAdmin;