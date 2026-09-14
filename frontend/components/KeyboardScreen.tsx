import React from "react";
import {
  KeyboardAvoidingView,
  Platform,
  StyleSheet,
  View,
} from "react-native";

type Props = {
  children: React.ReactNode;
};

export default function KeyboardScreen({
  children,
}: Props) {
  return (
    <View style={styles.container}>
      {children}
    </View>
  );
}

export function KeyboardWhiteContainer({
  children,
}: Props) {
  return (
    <KeyboardAvoidingView
      style={styles.keyboardContainer}
      behavior={Platform.OS === "ios" ? "position" : "height"}
      keyboardVerticalOffset={0}
    >
      <View style={styles.whiteContainer}>
        {children}
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#FFFFFF",
  },

  keyboardContainer: {
    backgroundColor: "transparent",
    marginTop: -30,
    borderTopLeftRadius: 30,
    borderTopRightRadius: 30,
  },

  whiteContainer: {
    backgroundColor: "#FFFFFF",
    borderTopLeftRadius: 30,
    borderTopRightRadius: 30,
    overflow: "hidden",
  },
});