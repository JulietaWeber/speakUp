const jwt = require("jsonwebtoken");

const verificarToken = (req, res, next) => {
  try {
    const authHeader = req.headers.authorization;

    if (!authHeader) {
      return res.status(401).json({
        data: null,
        error: "Falta token de autorización"
      });
    }

    const partes = authHeader.split(" ");

    if (partes.length !== 2 || partes[0] !== "Bearer") {
      return res.status(401).json({
        data: null,
        error: "Formato de token inválido"
      });
    }

    const token = partes[1];

    const decoded = jwt.verify(token, process.env.JWT_SECRET);

    req.usuario = {
      id_usuario: decoded.id_usuario,
      email: decoded.email,
      rol: decoded.rol
    };

    next();

  } catch (error) {
    return res.status(401).json({
      data: null,
      error: "Token inválido o expirado"
    });
  }
};

module.exports = verificarToken;