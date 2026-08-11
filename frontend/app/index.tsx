import { Redirect } from "expo-router";

//redirigir automáticamente al usuario a otra pantalla.

export default function Index() {
  return <Redirect href="/register" />;
} 

//Defino la pantalla inicial