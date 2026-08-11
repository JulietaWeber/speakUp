const express = require("express");
const router = express.Router();

const {
  pingIA,
  predecirSiguientePalabra,
  corregirFrase,
  procesarFraseConIA
} = require("../controllers/ia.controller");

const verificarToken = require("../middlewares/auth.middleware");

router.get("/ping", pingIA);

router.post("/predecir", verificarToken, predecirSiguientePalabra);
router.post("/corregir", verificarToken, corregirFrase);
router.post("/procesar-frase", verificarToken, procesarFraseConIA);

module.exports = router;