import { Stack } from "expo-router";

//Sistema de navegación que organiza las pantallas en pila --> se coloca encima de la anterior y permite volver atrás manteniendo el historial de navegación.

export default function Layout() {
  return (
    <Stack
      screenOptions={{
        headerShown: true, 
      }}
    />
  );
}

//Están las reglas que tienen que cumplir todas las pantallas