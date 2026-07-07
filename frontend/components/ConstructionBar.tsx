import { View, Text, StyleSheet, TouchableOpacity } from "react-native";
import { useConstruction } from "../context/ConstructionContext";

export default function ConstructionBar() {
  const { palabras, borrarUltimaPalabra, limpiar } = useConstruction();

  return (
    <View style={styles.container}>

      <View style={styles.topRow}>

        <View style={styles.wordsContainer}>
          <Text style={styles.text}>
            {palabras.join(" ")}
          </Text>
        </View>

        <TouchableOpacity
          onPress={borrarUltimaPalabra}
          style={styles.deleteButton}
        >
          <Text style={styles.deleteText}>✕</Text>
        </TouchableOpacity>

      </View>

      {palabras.length > 0 && (
        <TouchableOpacity
          onPress={limpiar}
          style={styles.clearButton}
        >
          <Text style={styles.clearText}>Reiniciar oración</Text>
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