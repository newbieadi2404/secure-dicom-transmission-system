from secure_med_trans.security.secure_package import SecurePackage

package = SecurePackage.extract("output/package.smt")

print("HEADER SENDER:", package["header"]["security"]["sender"])