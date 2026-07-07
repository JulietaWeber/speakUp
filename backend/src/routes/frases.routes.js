const express = require("express");
const router = express.Router();

const {
  armarFrase
} = require("../controllers/frases.controller");

router.post("/armar", armarFrase);

module.exports = router;