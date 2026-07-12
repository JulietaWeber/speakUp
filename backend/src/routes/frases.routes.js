const express = require("express");
const router = express.Router();

const {
  armarFrase
} = require("../controllers/frases.controller");

const verificarToken = require("../middlewares/auth.middleware");

router.post("/armar", verificarToken, armarFrase);

module.exports = router;