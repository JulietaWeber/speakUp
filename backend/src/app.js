process.env.NODE_TLS_REJECT_UNAUTHORIZED = "0";

require("dotenv").config();

const express = require("express");
const cors = require("cors");

const usuariosRoutes = require("./routes/usuarios.routes");
const tablerosRoutes = require("./routes/tableros.routes");

const app = express();

app.use(cors());
app.use(express.json());

app.get("/", (req, res) => {
  res.send("SpeakUp backend funcionando");
});

app.use("/usuarios", usuariosRoutes);
app.use("/tableros", tablerosRoutes);

app.listen(3000, () => {
  console.log("Servidor corriendo en puerto 3000");
});