import { View, Text, StyleSheet } from "react-native";

export default function SuggestionsBar() {
  return (
    <View style={styles.container}>
      <Text style={styles.title}>Sugeridos</Text>

      <View style={styles.suggestionsContainer}>
        <Text style={styles.emptyText}>
          No hay sugerencias todavía.
        </Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: "#FFFFFF",
    borderRadius: 15,
    padding: 10,
    marginBottom: 15,
    elevation: 3,
  },

  title: {
    fontSize: 18,
    fontWeight: "bold",
    color: "#356879",
    marginBottom: 10,
  },

  suggestionsContainer: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 10,
  },

  emptyText: {
    color: "#8A969A",
    fontSize: 14,
  },
});