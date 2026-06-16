const express = require("express");

const router = express.Router();

const {
  obtenerPictogramas,
  crearPictograma,
  obtenerPictogramaPorId,
  actualizarPictograma,
  eliminarPictograma,
  obtenerPictogramasPorCategoria,
  obtenerPictogramasPersonalizados
} = require("../controllers/pictogramas.controller");

router.get("/", obtenerPictogramas);

router.post("/", crearPictograma);

router.get(
  "/personalizados",
  obtenerPictogramasPersonalizados
);

router.get(
  "/categoria/:id",
  obtenerPictogramasPorCategoria
);

router.get("/:id", obtenerPictogramaPorId);

router.put("/:id", actualizarPictograma);

router.delete("/:id", eliminarPictograma);

module.exports = router;