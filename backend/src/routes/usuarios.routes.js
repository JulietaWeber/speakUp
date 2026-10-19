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
  obtenerPerfil,
  actualizarVozPreferida
} = require("../controllers/usuarios.controller");

// Las rutas de usuarios requieren autenticación, también las que antes eran públicas.
router.use(verificarToken);

router.get("/perfil/me", obtenerPerfil);
router.put("/voz", actualizarVozPreferida);
router.post("/foto-perfil", upload.single("foto"), subirFotoPerfil);
router.delete("/foto-perfil", eliminarFotoPerfil);

router.get("/", obtenerUsuarios);
router.post("/", crearUsuario);
router.get("/:id/tableros", obtenerTablerosDeUsuario);
router.get("/:id", obtenerUsuarioPorId);
router.put("/:id", actualizarUsuario);
router.delete("/:id", eliminarUsuario);

module.exports = router;