const supabase = require("../config/Supabase");

const obtenerUsuarios = async (req, res) => {

  const { data, error } = await supabase
    .from("usuarios")
    .select("*");

  res.json({ data, error });

};

const crearUsuario = async (req, res) => {

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

  res.json({
    message: "Usuario creado correctamente",
    data,
    error
  });

};

module.exports = {
  obtenerUsuarios,
  crearUsuario
};