const multer = require("multer");

const storage = multer.memoryStorage();

const fileFilter = (req, file, callback) => {
  const tiposPermitidos = ["image/jpeg", "image/png", "image/webp"];

  if (tiposPermitidos.includes(file.mimetype)) {
    callback(null, true);
  } else {
    callback(new Error("Solo se permiten imágenes JPG, PNG o WEBP"), false);
  }
};

const upload = multer({
  storage,
  fileFilter,
  limits: {
    fileSize: 2 * 1024 * 1024
  }
});

module.exports = upload;