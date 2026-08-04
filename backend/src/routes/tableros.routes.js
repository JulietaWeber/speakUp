const express = require("express");
const router = express.Router();

const {
  obtenerMisTableros,
  crearTablero,
  obtenerPictogramasDeTablero,
  agregarPictogramaATablero,
  eliminarPictogramaDeTablero,
  obtenerTableroCompleto,
  actualizarTablero,
  eliminarTablero
} = require("../controllers/tableros.controller");

const verificarToken = require("../middlewares/auth.middleware");

router.get("/mis-tableros", verificarToken, obtenerMisTableros);
router.post("/", verificarToken, crearTablero);

router.get("/:id_tablero/completo", verificarToken, obtenerTableroCompleto);

router.get("/:id_tablero/pictogramas", verificarToken, obtenerPictogramasDeTablero);
router.post("/:id_tablero/pictogramas", verificarToken, agregarPictogramaATablero);
router.delete("/:id_tablero/pictogramas/:id_pictogramas", verificarToken, eliminarPictogramaDeTablero);

router.put("/:id_tablero", verificarToken, actualizarTablero);
router.delete("/:id_tablero", verificarToken, eliminarTablero);

module.exports = router;