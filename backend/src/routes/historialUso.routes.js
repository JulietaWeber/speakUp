const express = require("express");
const router = express.Router();

const {
  obtenerMiHistorial
} = require("../controllers/historialUso.controller");

const verificarToken = require("../middlewares/auth.middleware");

router.get("/me", verificarToken, obtenerMiHistorial);

module.exports = router;