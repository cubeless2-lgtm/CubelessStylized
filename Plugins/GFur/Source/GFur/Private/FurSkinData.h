// Copyright 2023 GiM s.r.o. All Rights Reserved.

#pragma once

#include "Engine/SkeletalMesh.h"
#include "FurData.h"

// FMorphGPUSkinVertex is in a private header in UE 5.7; replicate the layout here
struct FMorphGPUSkinVertex
{
	FVector3f DeltaPosition;
	FVector3f DeltaTangentZ;
};


/** Soft Skin Vertex */
template<EStaticMeshVertexTangentBasisType TangentBasisTypeT, EStaticMeshVertexUVType UVTypeT, bool bExtraBoneInfluencesT>
struct FFurSkinVertex : FFurStaticVertex<TangentBasisTypeT, UVTypeT>
{
	enum
	{
		NumInfluences = bExtraBoneInfluencesT ? MAX_TOTAL_INFLUENCES : MAX_INFLUENCES_PER_STREAM,
	};

	uint16			InfluenceBones[NumInfluences];
	uint16			InfluenceWeights[NumInfluences];
};

/** Fur Skin Data */
class FFurSkinData: public FFurData
{
public:
	static FFurSkinData* CreateFurData(int32 InFurLayerCount, int32 InLod, class UGFurComponent* InFurComponent);
	static void DestroyFurData(const TArray<FFurData*>& InFurDataArray);

	virtual void CreateVertexFactories(TArray<FFurVertexFactory*>& VertexFactories, FVertexBuffer* InMorphVertexBuffer, bool InPhysics, ERHIFeatureLevel::Type InFeatureLevel) override;

protected:
	USkeletalMesh* SkeletalMesh = nullptr;
	TArray<USkeletalMesh*> GuideMeshes;
	bool HasExtraBoneInfluences;

#if WITH_EDITORONLY_DATA
	FDelegateHandle FurSplinesChangeHandle;
	FDelegateHandle FurSplinesCombHandle;
	FDelegateHandle SkeletalMeshChangeHandle;
	TArray<FDelegateHandle> GuideMeshesChangeHandles;
#endif // WITH_EDITORONLY_DATA

	FFurSkinData() {}
	~FFurSkinData();

	void UnbindChangeDelegates();
	void Set(int32 InFurLayerCount, int32 InLod, class UGFurComponent* InFurComponent);

	bool Compare(int32 InFurLayerCount, int32 InLod, class UGFurComponent* InFurComponent);
	bool Similar(int32 InLod, class UGFurComponent* InFurComponent);

	void BuildFur(BuildType Build);

	template<EStaticMeshVertexTangentBasisType TangentBasisTypeT>
	void BuildFur(const FSkeletalMeshLODRenderData& LodRenderData, BuildType Build);
	template<EStaticMeshVertexTangentBasisType TangentBasisTypeT, EStaticMeshVertexUVType UVTypeT>
	void BuildFur(const FSkeletalMeshLODRenderData& LodRenderData, BuildType Build);
	template<EStaticMeshVertexTangentBasisType TangentBasisTypeT, EStaticMeshVertexUVType UVTypeT, bool bExtraBoneInfluencesT>
	void BuildFur(const FSkeletalMeshLODRenderData& LodRenderData, BuildType Build);

	void BuildFur(const TArray<uint32>& InVertexSet);
	template<EStaticMeshVertexTangentBasisType TangentBasisTypeT>
	void BuildFur(const FSkeletalMeshLODRenderData& LodRenderData, const TArray<uint32>& InVertexSet);
	template<EStaticMeshVertexTangentBasisType TangentBasisTypeT, EStaticMeshVertexUVType UVTypeT>
	void BuildFur(const FSkeletalMeshLODRenderData& LodRenderData, const TArray<uint32>& InVertexSet);
	template<EStaticMeshVertexTangentBasisType TangentBasisTypeT, EStaticMeshVertexUVType UVTypeT, bool bExtraBoneInfluencesT>
	void BuildFur(const FSkeletalMeshLODRenderData& LodRenderData, const TArray<uint32>& InVertexSet);
};

/** Generate Splines */
void GenerateSplines(UFurSplines* Splines, USkeletalMesh* InSkeletalMesh, int32 InLod, const TArray<USkeletalMesh*>& InGuideMeshes);
