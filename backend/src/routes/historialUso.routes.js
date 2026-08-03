const express = require("express");
const router = express.Router();

const {
  obtenerMiHistorial,
  obtenerResumenHistorial
} = require("../controllers/historialUso.controller");

const verificarToken = require("../middlewares/auth.middleware");

router.get("/me", verificarToken, obtenerMiHistorial);
router.get("/resumen", verificarToken, obtenerResumenHistorial);

module.exports = router;