import { Redirect } from "expo-router";

//redirigir automáticamente al usuario a otra pantalla.

export default function Index() {
  return <Redirect href="/login" />;
} 

//Defino la pantalla inicial