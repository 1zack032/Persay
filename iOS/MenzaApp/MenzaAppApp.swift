//
//  MenzaAppApp.swift
//  MenzaApp
//
//  Menza - Encrypted Messaging
//

import SwiftUI

@main
struct MenzaAppApp: App {
    @StateObject private var authService = AuthService()
    @StateObject private var themeManager = ThemeManager()
    
    var body: some Scene {
        WindowGroup {
            ContentView()
                .environmentObject(authService)
                .environmentObject(themeManager)
                .preferredColorScheme(themeManager.colorScheme)
        }
    }
}
