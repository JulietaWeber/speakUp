const express = require("express");

const router = express.Router();

const {
    obtenerTableros,
    crearTablero,
    obtenerTableroPorId,
    actualizarTablero,
    eliminarTablero
  } = require("../controllers/tableros.controller");

router.get("/", obtenerTableros);

router.post("/", crearTablero);

router.get("/:id", obtenerTableroPorId);

router.put("/:id", actualizarTablero);

router.delete("/:id", eliminarTablero);

module.exports = router;