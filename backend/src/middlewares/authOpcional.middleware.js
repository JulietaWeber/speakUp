const jwt = require("jsonwebtoken");

const verificarTokenOpcional = (req, res, next) => {
  try {
    const authHeader = req.headers.authorization;

    if (!authHeader) {
      return next();
    }

    const partes = authHeader.split(" ");

    if (partes.length !== 2 || partes[0] !== "Bearer") {
      return next();
    }

    const token = partes[1];
    const decoded = jwt.verify(token, process.env.JWT_SECRET);

    req.usuario = {
      id_usuario: decoded.id_usuario,
      email: decoded.email,
      rol: decoded.rol
    };

    return next();

  } catch (error) {
    return next();
  }
};

module.exports = verificarTokenOpcional;