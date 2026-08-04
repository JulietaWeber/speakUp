const express = require("express");
const router = express.Router();

const {
  armarFrase,
  obtenerMisFrases,
  obtenerFrasePorId,
  eliminarFrase
} = require("../controllers/frases.controller");

const verificarToken = require("../middlewares/auth.middleware");

router.post("/armar", verificarToken, armarFrase);
router.get("/mis-frases", verificarToken, obtenerMisFrases);

router.get("/:id_frase", verificarToken, obtenerFrasePorId);
router.delete("/:id_frase", verificarToken, eliminarFrase);

module.exports = router;