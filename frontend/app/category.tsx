import { useLocalSearchParams } from "expo-router";
import CategoryScreen from "../components/CategoryScreen";

export default function Category() {
  const { id, nombre, color } = useLocalSearchParams();

  return (
    <CategoryScreen
      titulo={nombre as string}
      idCategoria={Number(id)}
      color={color as string}
    />
  );
}