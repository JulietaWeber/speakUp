const express = require("express");

const router = express.Router();

const {
  registrarUsuario,
  loginUsuario,
  loginGoogle,
  obtenerMiPerfil
} = require("../controllers/auth.controller");

const verificarToken = require("../middlewares/auth.middleware");

router.post("/register", registrarUsuario);

router.post("/login", loginUsuario);

router.post("/google", loginGoogle);

router.get("/me", verificarToken, obtenerMiPerfil);

module.exports = router;