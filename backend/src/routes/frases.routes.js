const express = require("express");
const router = express.Router();

const {
  armarFrase,
  obtenerMisFrases
} = require("../controllers/frases.controller");

const verificarToken = require("../middlewares/auth.middleware");

router.post("/armar", verificarToken, armarFrase);
router.get("/mis-frases", verificarToken, obtenerMisFrases);

module.exports = router;