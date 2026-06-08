const express = require("express");

const router = express.Router();

const {
    obtenerCategorias,
    crearCategoria,
    obtenerCategoriaPorId,
    actualizarCategoria,
    eliminarCategoria,
    obtenerPictogramasDeCategoria
  } = require("../controllers/categorias.controller");

router.get("/", obtenerCategorias);

router.post("/", crearCategoria);

router.get("/:id/pictogramas", obtenerPictogramasDeCategoria);

router.get("/:id", obtenerCategoriaPorId);

router.put("/:id", actualizarCategoria);

router.delete("/:id", eliminarCategoria);

module.exports = router;