const express = require("express");
const router = express.Router();

const {
  obtenerMisTableros,
  crearTablero,
  obtenerPictogramasDeTablero,
  agregarPictogramaATablero,
  eliminarPictogramaDeTablero
} = require("../controllers/tableros.controller");

const verificarToken = require("../middlewares/auth.middleware");

router.get("/mis-tableros", verificarToken, obtenerMisTableros);
router.post("/", verificarToken, crearTablero);

router.get("/:id_tablero/pictogramas", verificarToken, obtenerPictogramasDeTablero);
router.post("/:id_tablero/pictogramas", verificarToken, agregarPictogramaATablero);
router.delete("/:id_tablero/pictogramas/:id_pictogramas", verificarToken, eliminarPictogramaDeTablero);

module.exports = router;