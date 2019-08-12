module Main exposing ( main )

import Array
import Browser
import Browser.Events as Events
import Dict exposing ( Dict )
import File exposing ( File )
import File.Download as Download
import File.Select as Select
import Html exposing ( Html, div, text, button, input, label, pre, span, p )
import Html.Attributes exposing ( class, type_, for, id, disabled, value, name, checked )
import Html.Events exposing ( onClick, onInput, on )
import Json.Decode as Decode
import Json.Encode as Encode
import Task
import Set


main = Browser.document
    { init = init
    , view = view
    , update = update
    , subscriptions = subscriptions
    }


-- MODEL

type Filename = Filename String
type Repository = Repository String

type DocstringType
    = Google
    | Sphinx

type Metadata =
    Metadata
        (List String)
        (List String)
        (List String)
        (List String)
        (List String)

type MetadataType
    = Arguments
    | Raises
    | Variables
    | Sections
    | Noqas

getMetadata : MetadataType -> Metadata -> List String
getMetadata metadatatype =
    let
        getter (Metadata args raises variables sections noqas) =
            case metadatatype of
                Arguments ->
                    args
                Raises ->
                    raises
                Variables ->
                    variables
                Sections ->
                    sections
                Noqas ->
                    noqas
    in
        getter


setMetadata : MetadataType -> Metadata -> List String -> Metadata
setMetadata metadatatype (Metadata args raises variables sections noqas) section =
    case metadatatype of
        Arguments ->
            Metadata section raises variables sections noqas
        Raises ->
            Metadata args section variables sections noqas
        Variables ->
            Metadata args raises section sections noqas
        Sections ->
            Metadata args raises variables section noqas
        Noqas ->
            Metadata args raises variables sections section


type Docstring =
    Docstring
        Repository
        Filename
        (Maybe String)
        Metadata
        DocstringType

type alias Model =
    { docstrings : Array.Array Docstring
    , selected : Int
    , error : Maybe String
    -- The target where we want to place items.
    , target : Maybe MetadataType
    , customEntry : String
    }

type alias Flags =
    {}

init : Flags -> ( Model, Cmd Msg )
init flags =
    ( Model Array.empty -1 Nothing Nothing ""
    , Cmd.none
    )


removeMetadatum : Docstring -> MetadataType -> Int -> Docstring
removeMetadatum (Docstring repo filename doc metadata docstringType)
                metadataType
                index =
    let
        oldMetadataList =
            getMetadata metadataType metadata

        indexableOldMetadata =
            Array.fromList oldMetadataList

        withoutIndexed =
            Array.append
                (Array.slice 0 index indexableOldMetadata)
                (Array.slice
                    (index + 1)
                    (Array.length indexableOldMetadata)
                    indexableOldMetadata)

        newMetadataList =
            Array.toList withoutIndexed

        newMetadata =
            setMetadata metadataType metadata newMetadataList
    in
        Docstring repo filename doc newMetadata docstringType


nextTarget : Model -> Model
nextTarget model =
    case model.target of
        Nothing ->
            model
        Just target ->
            case target of
                Arguments ->
                    { model | target = Just Raises }
                Raises ->
                    { model | target = Just Variables }
                Variables ->
                    { model | target = Just Sections }
                Sections ->
                    { model | target = Just Noqas }
                Noqas ->
                    model

prevTarget : Model -> Model
prevTarget model =
    case model.target of
        Nothing ->
            model
        Just target ->
            case target of
                Arguments ->
                    model
                Raises ->
                    { model | target = Just Arguments }
                Variables ->
                    { model | target = Just Raises }
                Sections ->
                    { model | target = Just Variables }
                Noqas ->
                    { model | target = Just Sections }

-- DECODERS

filenameDecoder : Decode.Decoder Filename
filenameDecoder =
    Decode.map
        Filename
        Decode.string

repositoryDecoder : Decode.Decoder Repository
repositoryDecoder =
    Decode.map
        Repository
        Decode.string

decodeMetadata : Decode.Decoder Metadata
decodeMetadata =
    let
        sectionDecoder = Decode.list Decode.string
    in
    Decode.map5 Metadata
        (Decode.field "arguments" sectionDecoder)
        (Decode.field "raises" sectionDecoder)
        (Decode.field "variables" sectionDecoder)
        (Decode.field "sections" sectionDecoder)
        (Decode.field "noqas" sectionDecoder)

docstringTypeDecoder : Decode.Decoder DocstringType
docstringTypeDecoder =
    let
        stringToDocstringType s =
            case s of
                "SPHINX" ->
                    Sphinx
                _ ->
                    Google
    in
        Decode.map stringToDocstringType Decode.string

docstringDecoder : Decode.Decoder Docstring
docstringDecoder =
    Decode.map5 Docstring
        (Decode.field "repository" repositoryDecoder)
        (Decode.field "filename" filenameDecoder)
        (Decode.field "docstring" (Decode.maybe Decode.string))
        (Decode.field "metadata" decodeMetadata)
        (Decode.field "type" docstringTypeDecoder)


-- Decoders for the file and its contents.

fileDecoder : Decode.Decoder File
fileDecoder =
    Decode.at
        ["target", "files"]
        File.decoder

fileContentsDecoder : Decode.Decoder (Array.Array Docstring)
fileContentsDecoder =
    Decode.map Array.fromList
        <| Decode.list docstringDecoder


docstringEncoder : Docstring -> Encode.Value
docstringEncoder (Docstring
                    (Repository repo)
                    (Filename filename)
                    maybeDoc
                    metadata
                    docstringType) =
    let
        docstring =
            case maybeDoc of
                Nothing ->
                    Encode.null
                Just doc ->
                    Encode.string doc

        sectionEncoder =
            Encode.list Encode.string

        metadataEncoder (Metadata args raises variables sections noqas) =
            Encode.object
                [ ("arguments", sectionEncoder args)
                , ("raises", sectionEncoder raises)
                , ("variables", sectionEncoder variables)
                , ("sections", sectionEncoder sections)
                , ("noqas", sectionEncoder noqas)
                ]

        docstringTypeEncoder d =
            case d of
                Google ->
                    Encode.string "GOOGLE"
                Sphinx ->
                    Encode.string "SPHINX"
    in
    Encode.object
        [ ( "repository", Encode.string repo )
        , ( "filename", Encode.string filename )
        , ( "docstring", docstring )
        , ( "metadata", metadataEncoder metadata )
        , ( "type", docstringTypeEncoder docstringType )
        ]


-- UPDATE

type Msg
    = RequestFile
    | FileSelected File
    | FileLoaded String
    | UpdatePage String
    | Save
    -- Actions related to docstrings
    | Delete
    | SetTarget MetadataType
    | AddToTarget String Bool
    | RemoveFromTarget MetadataType Int
    | Noop
    | UpdateCustomEntry String
    | AddCustomEntry
    | KeyChanged String
    | ToggleDocstringType

update : Msg -> Model -> ( Model, Cmd Msg )
update msg model =
    case msg of
        RequestFile ->
            ( model
            , Select.file ["text/json"] FileSelected
            )
        FileSelected file ->
            ( model
            , Task.perform FileLoaded (File.toString file)
            )
        FileLoaded fileContents ->
            case Decode.decodeString fileContentsDecoder fileContents of
                Ok (contents) ->
                    ( { model
                        | docstrings = contents
                        , selected = 0
                      }
                    , Cmd.none
                    )
                Err err ->
                    ( { model
                        | error = Just <| Decode.errorToString err
                      }
                    , Cmd.none
                    )
        UpdatePage strValue ->
            case String.toInt strValue of
                Just page ->
                    ( { model
                        | selected = page
                      }
                    , Cmd.none
                    )
                Nothing ->
                    ( model, Cmd.none )
        Save ->
            ( model
            , Download.string
                "output.json"
                "text/json"
                <| Encode.encode 0
                <| (Encode.list docstringEncoder)
                <| Array.toList
                    model.docstrings
            )
        Delete ->
            let
                canDelete =
                    (not <| Array.isEmpty model.docstrings)
                    && model.selected >= 0
                    && model.selected < Array.length model.docstrings

                newDocstrings =
                    if canDelete then
                        Array.append
                          (Array.slice 0 model.selected model.docstrings)
                          (Array.slice
                            (model.selected + 1)
                            (Array.length model.docstrings)
                            model.docstrings)
                    else
                        model.docstrings
            in
            ( { model | docstrings = newDocstrings }
            , Cmd.none
            )
        SetTarget metadataType ->
            ( { model | target = Just metadataType }, Cmd.none )
        AddToTarget value clean ->
            case model.target of
                Nothing ->
                    ( model, Cmd.none )
                Just section ->
                     case Array.get model.selected model.docstrings of
                        Nothing ->
                            ( model, Cmd.none )
                        Just docstring ->
                            case docstring of
                                Docstring a b c oldMetadata e ->
                                    let
                                        oldItems =
                                            getMetadata section oldMetadata

                                        newValue =
                                            if clean then
                                                removePunctuation value
                                            else
                                                value

                                        newItems =
                                            newValue :: oldItems

                                        newMetadata =
                                            setMetadata section oldMetadata newItems

                                        newDocstrings =
                                            Array.set
                                                model.selected
                                                (Docstring a b c newMetadata e)
                                                model.docstrings
                                    in
                                        ( { model | docstrings = newDocstrings }, Cmd.none )
        RemoveFromTarget metadataType index ->
            case Array.get model.selected model.docstrings of
                Nothing ->
                    ( model, Cmd.none )
                Just docstring ->
                    let
                        newDocstring =
                            removeMetadatum docstring metadataType index

                        newDocstrings =
                            Array.set
                                model.selected
                                newDocstring
                                model.docstrings
                    in
                    ( { model | docstrings = newDocstrings }
                    , Cmd.none
                    )
        Noop ->
            ( model, Cmd.none )

        UpdateCustomEntry value ->
            ( { model | customEntry = value }, Cmd.none )

        AddCustomEntry ->
            let
                addTask =
                    Task.perform
                         (\_ -> AddToTarget model.customEntry False)
                         <| Task.succeed ""
            in
            ( { model | customEntry = "" }
            , addTask
            )
        KeyChanged key ->
            case key of
                "ArrowRight" ->
                    let
                        currSize =
                            Array.length model.docstrings

                        newSelected =
                            if 1 + model.selected > (currSize - 1) then
                                model.selected
                            else
                                model.selected + 1
                    in
                    ( { model | selected = newSelected }, Cmd.none )
                "ArrowLeft" ->
                    let
                        newSelected =
                            if model.selected - 1 < 0 then
                                0
                            else
                                model.selected - 1
                    in
                    ( { model | selected = newSelected }, Cmd.none )
                "ArrowDown" ->
                    ( nextTarget model, Cmd.none )
                "ArrowUp" ->
                    ( prevTarget model, Cmd.none )
                _ ->
                    ( model, Cmd.none )
        ToggleDocstringType ->
            case Array.get model.selected model.docstrings of
                Nothing ->
                    ( model, Cmd.none )
                Just (Docstring
                        repo
                        filename
                        doc
                        metadata
                        docstringType) ->
                    let
                        newDocstringType =
                            case docstringType of
                                Google -> Sphinx
                                Sphinx -> Google

                        newDocstring =
                            Docstring
                                repo
                                filename
                                doc
                                metadata
                                newDocstringType

                        newDocstrings =
                            Array.set
                                model.selected
                                newDocstring
                                model.docstrings
                    in
                    ( { model | docstrings = newDocstrings }, Cmd.none )

-- VIEW

fileUpload : Html Msg
fileUpload =
    div
        []
        [ button
            [ onClick RequestFile
            ]
            [ text "Upload File"
            ]
        ]

loaderView : Model -> Html Msg
loaderView model =
    if Array.isEmpty model.docstrings then
        fileUpload
    else
        div [] []

saveView : Model -> Html Msg
saveView model =
    if Array.isEmpty model.docstrings then
        div [] []
    else
        button
            [ onClick Save
            ]
            [ text "Save" ]

errorView : Model -> Html Msg
errorView model =
    case model.error of
        Nothing ->
            div [] []
        Just error ->
            div [ class "errors" ] [ text error ]


docstringTypeView : DocstringType -> Html Msg
docstringTypeView docstringType =
    let
        onChange msg =
          on "change" <| Decode.succeed msg
    in
    div
        [ class "docstring-type"
        ]
        [ label
            [ for "google-docstring-type"
            ]
            [ text "Google"
            ]
        , input
            [ type_ "radio"
            , id "google-docstring-type"
            , name "docstring-type"
            , value "Google"
            , checked <| docstringType == Google
            , onChange ToggleDocstringType
            ]
            []
        , label
            [ for "sphinx-docstring-type"
            ]
            [ text "Sphinx"
            ]
        , input
            [ type_ "radio"
            , id "sphinx-docstring-type"
            , name "docstring-type"
            , value "Sphinx"
            , checked <| docstringType == Sphinx
            , onChange ToggleDocstringType
            ]
            []
        ]


docstringView : Model -> Docstring -> Html Msg
docstringView model (Docstring
                        (Repository repo)
                        (Filename filename)
                        maybeDocstring
                        metadata
                        docstringType) =
    let
        wordView x =
            if String.isEmpty x then
                span [ class "indent" ] []
            else
                span
                    [ class "word"
                    , onClick <| AddToTarget x True
                    ]
                    [ text x ]

        lineView words =
            div [ class "line" ]
                <| List.map wordView words
    in
    case maybeDocstring of
        Nothing ->
            div [] []
        Just docstring ->
            div
                [ class "docstring-container " ]
                [ div
                    [ class "docstring" ]
                    <| List.map lineView
                    <| parseDocstring docstring
                , div
                    [ class "metadata-container"
                    ]
                    [ docstringTypeView docstringType
                    , metadataView metadata model.target
                    ]
                ]


metadataView : Metadata -> Maybe MetadataType -> Html Msg
metadataView metadata target =
    let
        sectionToString section =
            case section of
                Arguments -> "Arguments"
                Raises -> "Raises"
                Variables -> "Variables"
                Sections -> "Sections"
                Noqas -> "Noqas"

        dropBox section =
            let
                dropboxClass =
                    if target == (Just section) then
                            "dropbox selected"
                        else
                            "dropbox"

                metadatumView index metadatum =
                    div
                        [ class "metadatum"
                        , onClick <| RemoveFromTarget section index
                        ]
                        [ text metadatum ]

            in
            div
                [ class dropboxClass ]
                <| (++)
                    [ div
                        [ class "section-title"
                        , onClick <| SetTarget section
                        ]
                        [ text <| sectionToString section ]
                    ]
                <| List.indexedMap
                    metadatumView
                    <| getMetadata section metadata
    in
    div
        [ class "metadata" ]
        [ dropBox Arguments
        , dropBox Raises
        , dropBox Variables
        , dropBox Sections
        , dropBox Noqas
        ]

editView : Model -> Html Msg
editView model =
    let
        mainContents =
            case Array.get model.selected model.docstrings of
                Nothing ->
                    div [] []
                Just docstring ->
                    docstringView model docstring

        currentPage =
            model.selected

        disableNextPage =
            currentPage + 1 >= Array.length model.docstrings

        disablePrevPage =
            currentPage <= 0

        disableCustomEntry =
            model.target == Nothing

        actionsPane =
            div
                [ class "actions" ]
                [ div
                    []
                    [ input
                        [ type_ "text"
                        , id "custom-entry"
                        , disabled disableCustomEntry
                        , onInput <| UpdateCustomEntry
                        , value model.customEntry
                        ]
                        []
                    , button
                        [ class "custom-entry-ok"
                        , disabled disableCustomEntry
                        , onClick AddCustomEntry
                        ]
                        [ text "✓" ]
                    ]
                , div
                    [ onClick <| AddToTarget "short-description" False
                    , class "default-entry"
                    ]
                    [ text "short-description" ]
                , div
                    [ onClick <| AddToTarget "long-description" False
                    , class "default-entry"
                    ]
                    [ text "long-description" ]
                , div
                    [ onClick <| AddToTarget "*" False
                    , class "default-entry"
                    ]
                    [ text "*" ]
                , button
                    [ class "delete"
                    , onClick Delete ]
                    [ text "X"
                    ]
                ]

        selector =
            div
                [ class "selector" ]
                [ button
                    [ disabled disablePrevPage
                    , onClick <|
                        UpdatePage (String.fromInt <| currentPage - 1)
                    ]
                    [ text "←" ]
                , div
                    [ class "page-number" ]
                    [ div
                        []
                        [ label [ for "Number" ] [ text "" ]
                        , input
                            [ type_ "number"
                            , id "Number"
                            , value <| String.fromInt model.selected
                            , onInput UpdatePage
                            ]
                            [ ]
                        ]
                    , span
                        []
                        [ text <|
                            "/" ++ String.fromInt (Array.length model.docstrings)
                        ]
                    ]
                , button
                    [ disabled disableNextPage
                    , onClick <|
                        UpdatePage (String.fromInt <| currentPage + 1)
                    ]
                    [ text "→" ]
                ]
    in
        if Array.isEmpty model.docstrings then
            div [ class "main-content" ] []
        else
            div
                [ class "main-content" ]
                [ actionsPane
                , mainContents
                , selector
                ]

view : Model -> Browser.Document Msg
view model =
    Browser.Document
        "Docstring classifier"
            [ loaderView model
            , editView model
            , errorView model
            , saveView model
            ]


-- SUBSCRIPTIONS

subscriptions : Model -> Sub Msg
subscriptions model =
    Events.onKeyUp <|
        Decode.map KeyChanged <|
            Decode.field "key" Decode.string


-- Parser
parseDocstring : String -> List (List String)
parseDocstring docstring =
    let
        doUntilNoChange f x =
            if f x == x then
                x
            else
                doUntilNoChange f (f x)

        removeDoubleSpaces =
            doUntilNoChange (String.replace "  " " ")

        join = List.foldr (++) []

        separate =
            join
            << List.map (String.split " ")
            << List.map removeDoubleSpaces
            << String.split "    "
    in
        List.map separate
        <| String.lines docstring


{-| Removes all disallowed punctuation from a word.

This is not very discriminatory, simply takes all allowed
identifier components, and lets them through.  So, if it's
actually two words separated by punctuation, it will still
look like one word.

-}
removePunctuation : String -> String
removePunctuation word =
    let
        allowed =
            Set.fromList
            <| String.toList
            <| "abcdefghijklmnopqrstuvwxyz"
            ++ "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
            ++ "0123456789"
            ++ "_"

        isAllowed x =
            Set.member
                x
                allowed

        (trimmedWord, _) =
            List.partition isAllowed
            <| String.toList word
    in
        String.fromList trimmedWord
