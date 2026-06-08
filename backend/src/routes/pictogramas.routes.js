const express = require("express");

const router = express.Router();

const {
  obtenerPictogramas,
  crearPictograma,
  obtenerPictogramaPorId,
  actualizarPictograma,
  eliminarPictograma
} = require("../controllers/pictogramas.controller");

router.get("/", obtenerPictogramas);

router.post("/", crearPictograma);

router.get("/:id", obtenerPictogramaPorId);

router.put("/:id", actualizarPictograma);

router.delete("/:id", eliminarPictograma);

module.exports = router;