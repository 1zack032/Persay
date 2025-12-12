//
//  Theme.swift
//  MenzaApp
//
//  Theme and color management
//

import SwiftUI

// MARK: - Theme Manager
class ThemeManager: ObservableObject {
    @Published var isDarkMode: Bool {
        didSet {
            UserDefaults.standard.set(isDarkMode, forKey: "isDarkMode")
        }
    }
    
    var colorScheme: ColorScheme? {
        isDarkMode ? .dark : .light
    }
    
    init() {
        // Default to dark mode on first launch
        if UserDefaults.standard.object(forKey: "isDarkMode") == nil {
            self.isDarkMode = true  // Dark mode by default
            UserDefaults.standard.set(true, forKey: "isDarkMode")
        } else {
            self.isDarkMode = UserDefaults.standard.bool(forKey: "isDarkMode")
        }
    }
    
    func toggle() {
        isDarkMode.toggle()
    }
}

// MARK: - Menza Colors
extension Color {
    // Primary colors
    static let menzaPurple = Color(hex: "7c3aed")
    static let menzaPurpleLight = Color(hex: "a855f7")
    static let menzaPink = Color(hex: "ec4899")
    
    // Background colors
    static let menzaBgDark = Color(hex: "030306")
    static let menzaBgSecondary = Color(hex: "08080c")
    static let menzaCard = Color(hex: "0c0c12")
    
    // Light mode
    static let menzaBgLight = Color(hex: "f5f5f7")
    static let menzaCardLight = Color.white
    
    // Text colors
    static let menzaTextPrimary = Color.primary
    static let menzaTextSecondary = Color.secondary
    
    // Status colors
    static let menzaSuccess = Color(hex: "10b981")
    static let menzaWarning = Color(hex: "f59e0b")
    static let menzaError = Color(hex: "ef4444")
    
    // Initialize from hex
    init(hex: String) {
        let hex = hex.trimmingCharacters(in: CharacterSet.alphanumerics.inverted)
        var int: UInt64 = 0
        Scanner(string: hex).scanHexInt64(&int)
        let a, r, g, b: UInt64
        switch hex.count {
        case 3: // RGB (12-bit)
            (a, r, g, b) = (255, (int >> 8) * 17, (int >> 4 & 0xF) * 17, (int & 0xF) * 17)
        case 6: // RGB (24-bit)
            (a, r, g, b) = (255, int >> 16, int >> 8 & 0xFF, int & 0xFF)
        case 8: // ARGB (32-bit)
            (a, r, g, b) = (int >> 24, int >> 16 & 0xFF, int >> 8 & 0xFF, int & 0xFF)
        default:
            (a, r, g, b) = (255, 0, 0, 0)
        }
        self.init(
            .sRGB,
            red: Double(r) / 255,
            green: Double(g) / 255,
            blue: Double(b) / 255,
            opacity: Double(a) / 255
        )
    }
}

// MARK: - Custom Modifiers
struct MenzaButtonStyle: ButtonStyle {
    var isPrimary: Bool = true
    
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .font(.headline)
            .foregroundColor(Color.white)
            .frame(maxWidth: .infinity)
            .padding(.vertical, 16)
            .background(
                LinearGradient(
                    colors: isPrimary ? [.menzaPurple, .menzaPurpleLight] : [.gray.opacity(0.3)],
                    startPoint: .leading,
                    endPoint: .trailing
                )
            )
            .cornerRadius(25)
            .scaleEffect(configuration.isPressed ? 0.98 : 1.0)
            .animation(.easeInOut(duration: 0.1), value: configuration.isPressed)
    }
}

struct MenzaTextFieldStyle: TextFieldStyle {
    func _body(configuration: TextField<Self._Label>) -> some View {
        configuration
            .padding(.horizontal, 20)
            .padding(.vertical, 16)
            .background(Color(.systemGray6))
            .cornerRadius(25)
    }
}

// MARK: - View Extensions
extension View {
    func menzaCard() -> some View {
        self
            .padding()
            .background(Color(.systemBackground))
            .cornerRadius(16)
            .shadow(color: .black.opacity(0.1), radius: 10, x: 0, y: 4)
    }
    
    func menzaGradientBackground() -> some View {
        self.background(
            LinearGradient(
                colors: [Color.menzaBgDark, Color.menzaBgSecondary],
                startPoint: .top,
                endPoint: .bottom
            )
            .ignoresSafeArea()
        )
    }
}

