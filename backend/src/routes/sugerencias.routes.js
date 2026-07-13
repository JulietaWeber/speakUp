const express = require("express");
const router = express.Router();

const {
  obtenerSugerencias,
  obtenerMisSugerencias
} = require("../controllers/sugerencias.controller");

const verificarToken = require("../middlewares/auth.middleware");

router.post("/", verificarToken, obtenerSugerencias);
router.get("/mis-sugerencias", verificarToken, obtenerMisSugerencias);

module.exports = router;