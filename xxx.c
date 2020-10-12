#include <clang-c/Index.h>
int main() {
	const char* filename = "x.cpp";
	CXIndex clang_index = clang_createIndex(0, 0);
	CXTranslationUnit clang_translation_unit_ = NULL;
	clang_parseTranslationUnit2FullArgv( clang_index, filename, (const char*[]){"-xcpp"}, 1, NULL, 0, clang_defaultEditingTranslationUnitOptions(), &clang_translation_unit_ );
	clang_codeCompleteAt( clang_translation_unit_, filename, 1, 1, NULL, 0, clang_defaultCodeCompleteOptions());
}
