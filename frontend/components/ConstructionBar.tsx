import { View, Text, StyleSheet, TouchableOpacity } from "react-native";
import { useState, useEffect } from "react";
import AsyncStorage from "@react-native-async-storage/async-storage";
import { useConstruction } from "../context/ConstructionContext";
import { armarFrase } from "../services/api";

export default function ConstructionBar() {
  const { palabras, borrarUltimaPalabra, limpiar } = useConstruction();
  const [seleccionada, setSeleccionada] = useState(false);

  useEffect(() => {
    setSeleccionada(false);
  }, [palabras]);

  const confirmarOracion = async () => {
    if (palabras.length === 0) return;

    setSeleccionada(true);

    const idsPictogramas = palabras.map(
      (p) => p.id_pictogramas
    );

    const token = await AsyncStorage.getItem("token");

    const usuarioGuardado = await AsyncStorage.getItem("usuario");

    const usuario = usuarioGuardado
      ? JSON.parse(usuarioGuardado)
      : null;

    if (!usuario || !token) {
      console.log("No hay sesión iniciada");
      return;
    }

    try {
      const respuesta = await armarFrase(
        usuario.id_usuario,
        idsPictogramas,
        token
      );

      console.log("Frase creada:", respuesta);

      // Ya NO limpiamos la oración

    } catch (error) {
      console.log("Error enviando frase:", error);
    } finally {
      setSeleccionada(false);
    }
  };

  return (
    <View
      style={[
        styles.container,
        seleccionada && styles.containerSeleccionado,
      ]}
    >
      <TouchableOpacity
        activeOpacity={1}
        onPress={confirmarOracion}
        style={styles.wordsArea}
      >
        <View style={styles.topRow}>
          <View style={styles.wordsContainer}>
            <Text style={styles.text}>
              {palabras.map((p) => p.nombre).join(" ")}
            </Text>
          </View>

          <TouchableOpacity
            onPress={borrarUltimaPalabra}
            style={styles.deleteButton}
          >
            <Text style={styles.deleteText}>✕</Text>
          </TouchableOpacity>
        </View>
      </TouchableOpacity>

      {palabras.length > 0 && (
        <TouchableOpacity
          onPress={limpiar}
          style={styles.clearButton}
        >
          <Text style={styles.clearText}>
            Reiniciar oración
          </Text>
        </TouchableOpacity>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: "#fff",
    padding: 10,
    borderRadius: 15,
    marginBottom: 20,
    elevation: 3,
  },

  containerSeleccionado: {
    backgroundColor: "#bdbdbd",
  },

  wordsArea: {
    width: "100%",
  },

  topRow: {
    flexDirection: "row",
    alignItems: "center",
  },

  wordsContainer: {
    flex: 1,
  },

  text: {
    fontSize: 22,
  },

  deleteButton: {
    width: 40,
    height: 40,
    backgroundColor: "#8c8c8c",
    justifyContent: "center",
    alignItems: "center",
    borderRadius: 8,
    marginLeft: 10,
  },

  deleteText: {
    color: "white",
    fontSize: 24,
    fontWeight: "bold",
  },

  clearButton: {
    marginTop: 15,
    backgroundColor: "#ef4444",
    borderRadius: 10,
    padding: 10,
    alignItems: "center",
  },

  clearText: {
    color: "white",
    fontWeight: "bold",
    fontSize: 16,
  },
});