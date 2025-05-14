// 表关系类型
export enum RelationshipType {
    ONE_TO_ONE = "one_to_one",
    ONE_TO_MANY = "one_to_many",
    MANY_TO_MANY = "many_to_many",
    UNDEFINED = "undefined"
}

// 关系识别方法
export enum IdentificationMethod {
    AUTO = "auto",
    MANUAL = "manual"
} 