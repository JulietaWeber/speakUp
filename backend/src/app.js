NODE_TLS_REJECT_UNAUTHORIZED = "0"

require("dotenv").config();

const express = require("express");
const cors = require("cors");
const supabase = require("./Supabase");

const app = express();

app.use(cors());
app.use(express.json());

app.get("/", (req, res) => {
  res.send("SpeakUp backend funcionando");
});

// test-db (usuario)

app.get("/test-db", async (req, res) => {
    const { data, error } = await supabase.from("usuarios").select("*");
  
    res.json({ data, error });
  });

app.listen(3000, () => {
  console.log("Servidor corriendo en puerto 3000");
});

app.get("/test-db", async (req, res) => {
  const { data, error } = await supabase
    .from("users")
    .select("*");

  if (error) {
    return res.status(500).json({ error });
  }

  res.json(data);
});

app.post("/register", async (req, res) => {

  const {
    nombre,
    email,
    password,
    rol,
    foto_perfil,
    ultima_sincronizacion
  } = req.body;

  const { data, error } = await supabase
    .from("usuarios")
    .insert([
      {
        nombre,
        email,
        password,
        rol,
        foto_perfil,
        ultima_sincronizacion
      }
    ]);

  if (error) {
    return res.status(500).json({ error });
  }

  res.json({
    message: "Usuario creado correctamente",
    data
  });

});