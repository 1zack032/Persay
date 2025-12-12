//
//  User.swift
//  MenzaApp
//
//  User model for Menza
//

import Foundation

struct User: Codable, Identifiable {
    let id: String
    let username: String
    var displayName: String?
    var email: String?
    var phone: String?
    var profilePicture: String?
    var bio: String?
    var isPremium: Bool
    var isOnline: Bool
    var lastSeen: Date?
    var createdAt: Date
    
    enum CodingKeys: String, CodingKey {
        case id
        case username
        case displayName = "display_name"
        case email
        case phone
        case profilePicture = "profile_picture"
        case bio
        case isPremium = "premium"
        case isOnline = "is_online"
        case lastSeen = "last_seen"
        case createdAt = "created_at"
    }
    
    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        id = try container.decodeIfPresent(String.self, forKey: .id) ?? UUID().uuidString
        username = try container.decode(String.self, forKey: .username)
        displayName = try container.decodeIfPresent(String.self, forKey: .displayName)
        email = try container.decodeIfPresent(String.self, forKey: .email)
        phone = try container.decodeIfPresent(String.self, forKey: .phone)
        profilePicture = try container.decodeIfPresent(String.self, forKey: .profilePicture)
        bio = try container.decodeIfPresent(String.self, forKey: .bio)
        isPremium = try container.decodeIfPresent(Bool.self, forKey: .isPremium) ?? false
        isOnline = try container.decodeIfPresent(Bool.self, forKey: .isOnline) ?? false
        lastSeen = try container.decodeIfPresent(Date.self, forKey: .lastSeen)
        createdAt = try container.decodeIfPresent(Date.self, forKey: .createdAt) ?? Date()
    }
    
    // For creating local user
    init(username: String, displayName: String? = nil) {
        self.id = UUID().uuidString
        self.username = username
        self.displayName = displayName
        self.isPremium = false
        self.isOnline = true
        self.createdAt = Date()
    }
}

// MARK: - Auth Response
struct AuthResponse: Codable {
    let success: Bool
    let message: String?
    let user: User?
    let seedPhrase: String?
    
    enum CodingKeys: String, CodingKey {
        case success
        case message
        case user
        case seedPhrase = "seed_phrase"
    }
}

struct LoginRequest: Codable {
    let username: String
    let password: String
}

struct RegisterRequest: Codable {
    let username: String
    let password: String
    let email: String?
    
    let phone: String?
}

