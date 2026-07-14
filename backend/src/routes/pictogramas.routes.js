const express = require("express");
const router = express.Router();

const {
  obtenerPictogramas,
  obtenerPictogramasPorCategoria,
  crearPictograma,
  actualizarPictograma,
  eliminarPictograma,
  crearPictogramaPersonalizado,
  obtenerMisPictogramasPersonalizados,
  eliminarPictogramaPersonalizado
} = require("../controllers/pictogramas.controller");

const verificarToken = require("../middlewares/auth.middleware");

router.get("/", obtenerPictogramas);
router.get("/categoria/:id_categoria", obtenerPictogramasPorCategoria);

router.post("/personalizado", verificarToken, crearPictogramaPersonalizado);
router.get("/mis-personalizados", verificarToken, obtenerMisPictogramasPersonalizados);
router.delete("/personalizado/:id_pictograma", verificarToken, eliminarPictogramaPersonalizado);

router.post("/", crearPictograma);
router.put("/:id_pictograma", actualizarPictograma);
router.delete("/:id_pictograma", eliminarPictograma);

module.exports = router;