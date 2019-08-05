module Main exposing ( main )

import Array
import Browser
import Dict exposing ( Dict )
import File exposing ( File )
import File.Select as Select
import File.Download as Download
import Html exposing ( Html, div, text, button, input, label, pre, span, p )
import Html.Attributes exposing ( class, type_, for, id, disabled, value )
import Html.Events exposing ( onClick, onInput )
import Json.Decode as Decode
import Json.Encode as Encode
import Task


main = Browser.document
    { init = init
    , view = view
    , update = update
    , subscriptions = subscriptions
    }


-- MODEL

type Filename = Filename String
type Repository = Repository String

type Metadata =
    Metadata
        (List String)
        (List String)
        (List String)
        (List String)

type MetadataType
    = Arguments
    | Raises
    | Variables
    | Sections

getMetadata : MetadataType -> Metadata -> List String
getMetadata metadatatype =
    let
        getter (Metadata args raises variables sections) =
            case metadatatype of
                Arguments ->
                    args
                Raises ->
                    raises
                Variables ->
                    variables
                Sections ->
                    sections
    in
        getter


setMetadata : MetadataType -> Metadata -> List String -> Metadata
setMetadata metadatatype (Metadata args raises variables sections) section =
    case metadatatype of
        Arguments ->
            Metadata section raises variables sections
        Raises ->
            Metadata args section variables sections
        Variables ->
            Metadata args raises section sections
        Sections ->
            Metadata args raises variables section


type Docstring =
    Docstring
        Repository
        Filename
        (Maybe String)
        Metadata

type alias Model =
    { docstrings : Array.Array Docstring
    , selected : Int
    , error : Maybe String
    }

type alias Flags =
    {}

init : Flags -> ( Model, Cmd Msg )
init flags =
    ( Model Array.empty -1 Nothing
    , Cmd.none
    )


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
    Decode.map4 Metadata
        (Decode.field "arguments" sectionDecoder)
        (Decode.field "raises" sectionDecoder)
        (Decode.field "variables" sectionDecoder)
        (Decode.field "sections" sectionDecoder)

docstringDecoder : Decode.Decoder Docstring
docstringDecoder =
    Decode.map4 Docstring
        (Decode.field "repository" repositoryDecoder)
        (Decode.field "filename" filenameDecoder)
        (Decode.field "docstring" (Decode.maybe Decode.string))
        (Decode.field "metadata" decodeMetadata)


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
                    metadata) =
    let
        docstring =
            case maybeDoc of
                Nothing ->
                    Encode.null
                Just doc ->
                    Encode.string doc

        sectionEncoder =
            Encode.list Encode.string

        metadataEncoder (Metadata args raises variables sections) =
            Encode.object
                [ ("arguments", sectionEncoder args)
                , ("raises", sectionEncoder raises)
                , ("variables", sectionEncoder variables)
                , ("sections", sectionEncoder sections)
                ]
    in
    Encode.object
        [ ( "repository", Encode.string repo )
        , ( "filename", Encode.string filename )
        , ( "docstring", docstring )
        , ( "metadata", metadataEncoder metadata )
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

docstringView : Docstring -> Html Msg
docstringView (Docstring
                    (Repository repo)
                    (Filename filename)
                    maybeDocstring
                    metadata) =
    case maybeDocstring of
        Nothing ->
            div [] []
        Just docstring ->
            div
                [ class "docstring-container " ]
                [ pre
                    [ class "docstring" ]
                    [ text docstring
                    ]
                , metadataView metadata
                ]


metadataView : Metadata -> Html Msg
metadataView metadata =
    let
        sectionToString section =
            case section of
                Arguments -> "Arguments"
                Raises -> "Raises"
                Variables -> "Variables"
                Sections -> "Sections"

        dropBox section =
            div
                [ class "dropbox" ]
                <| (++)
                    [ div
                        [ class "section-title" ]
                        [ text <| sectionToString section ]
                    ]
                <| List.map
                    (\x -> div [] [ text x ])
                    <| getMetadata section metadata
    in
    div
        [ class "metadata" ]
        [ dropBox Arguments
        , dropBox Raises
        , dropBox Variables
        , dropBox Sections
        ]

editView : Model -> Html Msg
editView model =
    let
        mainContents =
            case Array.get model.selected model.docstrings of
                Nothing ->
                    div [] []
                Just docstring ->
                    docstringView docstring

        currentPage =
            model.selected

        disableNextPage =
            currentPage + 1 >= Array.length model.docstrings

        disablePrevPage =
            currentPage <= 0

        actionsPane =
            div
                [ class "actions" ]
                [ button
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
    Sub.none
