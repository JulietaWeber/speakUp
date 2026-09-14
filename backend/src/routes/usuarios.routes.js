const express = require("express");

const router = express.Router();

const verificarToken = require("../middlewares/auth.middleware");

const upload = require("../middlewares/upload.middleware");

const {
  obtenerUsuarios,
  crearUsuario,
  obtenerUsuarioPorId,
  actualizarUsuario,
  eliminarUsuario,
  obtenerTablerosDeUsuario,
  subirFotoPerfil,
  eliminarFotoPerfil,
  obtenerPerfil
} = require("../controllers/usuarios.controller");

// Rutas de perfil del usuario logueado
router.get("/perfil/me", verificarToken, obtenerPerfil);

router.post(
  "/foto-perfil",
  verificarToken,
  upload.single("foto"),
  subirFotoPerfil
);

router.delete(
  "/foto-perfil",
  verificarToken,
  eliminarFotoPerfil
);

// Rutas generales
router.get("/", obtenerUsuarios);

router.post("/", crearUsuario);

router.get("/:id/tableros", obtenerTablerosDeUsuario);

router.get("/:id", obtenerUsuarioPorId);

router.put("/:id", actualizarUsuario);

router.delete("/:id", eliminarUsuario);

module.exports = router;