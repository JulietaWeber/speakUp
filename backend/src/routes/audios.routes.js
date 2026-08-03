const express = require("express");
const router = express.Router();

const {
  crearAudio,
  obtenerMisAudios,
  obtenerAudioPorFrase,
  eliminarAudio
} = require("../controllers/audios.controller");

const verificarToken = require("../middlewares/auth.middleware");

router.post("/", verificarToken, crearAudio);
router.get("/mis-audios", verificarToken, obtenerMisAudios);
router.get("/frase/:id_frase", verificarToken, obtenerAudioPorFrase);
router.delete("/:id_audio", verificarToken, eliminarAudio);

module.exports = router;