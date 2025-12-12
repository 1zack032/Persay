//
//  Channel.swift
//  MenzaApp
//
//  Channel model for broadcasting
//

import Foundation

struct Channel: Codable, Identifiable, Equatable {
    let id: String
    var name: String
    var description: String?
    var avatar: String?
    let owner: String
    var subscriberCount: Int
    var isSubscribed: Bool
    var posts: [ChannelPost]?
    let createdAt: Date
    var category: String?
    var isVerified: Bool
    
    static func == (lhs: Channel, rhs: Channel) -> Bool {
        lhs.id == rhs.id
    }
    
    enum CodingKeys: String, CodingKey {
        case id
        case name
        case description
        case avatar
        case owner
        case subscriberCount = "subscriber_count"
        case isSubscribed = "is_subscribed"
        case posts
        case createdAt = "created_at"
        case category
        case isVerified = "is_verified"
    }
    
    // Explicit initializer for test data
    init(
        id: String = UUID().uuidString,
        name: String,
        description: String? = nil,
        avatar: String? = nil,
        owner: String = "",
        subscriberCount: Int = 0,
        isVerified: Bool = false,
        isSubscribed: Bool = false,
        posts: [ChannelPost]? = nil,
        createdAt: Date = Date(),
        category: String? = nil
    ) {
        self.id = id
        self.name = name
        self.description = description
        self.avatar = avatar
        self.owner = owner
        self.subscriberCount = subscriberCount
        self.isVerified = isVerified
        self.isSubscribed = isSubscribed
        self.posts = posts
        self.createdAt = createdAt
        self.category = category
    }
}

struct ChannelPost: Codable, Identifiable {
    let id: String
    let channelId: String
    let content: String
    let author: String
    var mediaUrls: [String]?
    var likes: Int
    var comments: Int
    var views: Int
    var isLiked: Bool
    let createdAt: Date
    
    enum CodingKeys: String, CodingKey {
        case id
        case channelId = "channel_id"
        case content
        case author
        case mediaUrls = "media_urls"
        case likes
        case comments
        case views
        case isLiked = "is_liked"
        case createdAt = "created_at"
    }
    
    // Explicit initializer for test data
    init(
        id: String = UUID().uuidString,
        channelId: String = "",
        content: String,
        author: String = "",
        mediaUrls: [String]? = nil,
        likes: Int = 0,
        comments: Int = 0,
        views: Int = 0,
        isLiked: Bool = false,
        createdAt: Date = Date()
    ) {
        self.id = id
        self.channelId = channelId
        self.content = content
        self.author = author
        self.mediaUrls = mediaUrls
        self.likes = likes
        self.comments = comments
        self.views = views
        self.isLiked = isLiked
        self.createdAt = createdAt
    }
}

struct ChannelComment: Codable, Identifiable {
    let id: String
    let postId: String
    let content: String
    let author: String
    var likes: Int
    let createdAt: Date
    
    enum CodingKeys: String, CodingKey {
        case id
        case postId = "post_id"
        case content
        case author
        case likes
        case createdAt = "created_at"
    }
}

