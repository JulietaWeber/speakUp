import React from "react";
import {
  KeyboardAvoidingView,
  Platform,
  ScrollView,
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
    <KeyboardAvoidingView
      style={styles.container}
      behavior={
        Platform.OS === "ios"
          ? "padding"
          : "height"
      }
      keyboardVerticalOffset={0}
    >
      <View style={styles.background}>
        <ScrollView
          style={styles.scroll}
          contentContainerStyle={styles.content}
          keyboardShouldPersistTaps="handled"
          showsVerticalScrollIndicator={false}
          automaticallyAdjustKeyboardInsets
        >
          {children}
        </ScrollView>
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#AFD4E8",
  },

  background: {
    flex: 1,
    backgroundColor: "#AFD4E8",
  },

  scroll: {
    flex: 1,
    backgroundColor: "#AFD4E8",
  },

  content: {
    flexGrow: 1,
    backgroundColor: "#AFD4E8",
  },
});